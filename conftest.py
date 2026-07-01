"""
pytest 全域設定
- 讀取 --site 參數
- 提供 site_config / page / logged_in_page / class_logged_in_page fixture
- 每個測試結束後自動登出（僅限 function-scoped page）

執行環境自動偵測：
- Windows：Playwright 直接啟動 Chrome（無需手動開瀏覽器）
- WSL/Linux：透過 CDP 連線到已開啟的 Windows Chrome（需設定 CDP_URL）

Fixture 選用指引：
  page                  — 每個測試獨立 context，測試後自動登出。適合 Smoke test。
  logged_in_page        — 同上，但已預先登入。適合 Smoke test 的登入後驗證。
  class_logged_in_page  — 一個 class 只登入一次，共用 session。適合功能型測試。
  go_home               — 搭配 class_logged_in_page，每個測試前回到首頁清理彈窗。
"""

import os
import sys
import socket
import subprocess
import time
import pytest
from urllib.parse import urlparse
from playwright.sync_api import Page, Playwright
from config.settings import get_site_config
from pages.factory import get_login_page_class, get_home_page_class
from utils.dialog_helper import dismiss_server_error_if_present
from utils.screenshot_helper import (
    ScreenshotHelper, attach_screenshotter, detach_screenshotter
)


def _is_wsl() -> bool:
    """偵測是否在 WSL 環境下執行"""
    if sys.platform != 'linux':
        return False
    try:
        with open('/proc/version', 'r') as f:
            return 'microsoft' in f.read().lower()
    except Exception:
        return False


def _is_ci() -> bool:
    """偵測是否在 CI 環境（GitHub Actions / 通用 CI runner 皆 export `CI=true`）"""
    return os.getenv("CI", "").lower() == "true"


def _is_cdp_ready(cdp_url: str) -> bool:
    """檢查 CDP port 是否已在監聽"""
    parsed = urlparse(cdp_url)
    host = parsed.hostname or '127.0.0.1'
    port = parsed.port or 9222
    try:
        with socket.create_connection((host, port), timeout=1):
            return True
    except OSError:
        return False


def _patch_playwright_crbrowser_sw_assert() -> bool:
    """
    Patch Playwright driver：讓 pre-existing service_worker target（沒有 browserContextId）
    不要觸發 assertion，改為靜默 detach。

    背景：若 Chrome 曾造訪過註冊 Service Worker 的站（例：dev-rc.t9platform.com），SW target
    在日後 CDP 重連時會被列出但 `browserContextId` 為空（default context，Chrome 不填該欄位）。
    Playwright crBrowser.js line 147 的 `assert(targetInfo.browserContextId, ...)` 因此 throw，
    整個 connect_over_cdp 掛掉，使用者被迫重啟 Chrome。

    本函式 idempotent：只在未 patch 時寫一次；已 patch 的 driver 直接 skip。
    若找不到目標行（例：Playwright 升版、檔案格式變動），安全跳過不阻擋測試。
    """
    import importlib.util

    try:
        spec = importlib.util.find_spec('playwright')
        if not spec or not spec.submodule_search_locations:
            return False
        pw_root = spec.submodule_search_locations[0]
    except Exception:
        return False

    cr_browser = os.path.join(
        pw_root, 'driver', 'package', 'lib', 'server', 'chromium', 'crBrowser.js'
    )
    if not os.path.isfile(cr_browser):
        return False

    try:
        with open(cr_browser, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception:
        return False

    marker = '__PW_SW_NO_CTX_PATCH__'
    if marker in content:
        return True  # 已 patch 過

    target_line = '(0, import_assert.assert)(targetInfo.browserContextId, "targetInfo: " + JSON.stringify(targetInfo, null, 2));'
    if target_line not in content:
        return False  # Playwright 版本不同，不動它

    replacement = (
        f'// {marker} — 容忍 pre-existing service_worker target 缺 browserContextId\n'
        '    if (!targetInfo.browserContextId) {\n'
        '      if (targetInfo.type === "service_worker") { session.detach().catch(() => {}); return; }\n'
        '      ' + target_line + '\n'
        '    }'
    )
    new_content = content.replace(target_line, replacement, 1)
    if new_content == content:
        return False

    try:
        with open(cr_browser, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f'[CDP] Playwright driver patched：容忍 stuck service worker（{cr_browser}）')
        return True
    except Exception as e:
        print(f'[CDP] Playwright driver patch 失敗，略過：{type(e).__name__}: {e}')
        return False


def _detach_stuck_service_workers(cdp_url: str) -> int:
    """
    Pre-flight：偵測 CDP 上 attached 的 service_worker target，逐一關閉。

    原因：若 Chrome 曾造訪過會註冊 Service Worker 的站（例：dev-rc.t9platform.com/sw.js），
    該 SW target 會以 attached=true 存在於既有 CDP。Playwright 的
    CRBrowser._onAttachedToTarget 對 service_worker 有「不應已 attached」的 assertion，
    直接 connect_over_cdp 會打到 assert → "Connection closed while reading from the driver"。

    實作：用 Chrome DevTools HTTP endpoint `/json` 列舉 targets，對 type=service_worker
    的項目呼叫 `/json/close/<targetId>`（HTTP，不需 WebSocket、不受 Chrome 的
    --remote-allow-origins 限制），關閉後 SW 就不再是 attached 狀態。

    失敗一律 silent（例：CDP 未開、網路錯）。

    Returns: 成功關閉的 SW 數量（0 代表沒 SW 或整段被跳過）。
    """
    try:
        import json
        import urllib.request
    except Exception:
        return 0

    try:
        list_url = cdp_url.rstrip('/') + '/json'
        with urllib.request.urlopen(list_url, timeout=2) as resp:
            targets = json.loads(resp.read())
    except Exception as e:
        print(f'[CDP] service worker 列舉失敗，略過：{type(e).__name__}: {e}')
        return 0

    sw_targets = [t for t in targets if t.get('type') == 'service_worker']
    if not sw_targets:
        return 0

    closed = 0
    for t in sw_targets:
        target_id = t.get('id')
        if not target_id:
            continue
        try:
            close_url = cdp_url.rstrip('/') + f'/json/close/{target_id}'
            with urllib.request.urlopen(close_url, timeout=2) as resp:
                if resp.status == 200:
                    closed += 1
        except Exception:
            pass  # 單一 SW 關不掉不影響整體流程

    if closed:
        print(f'[CDP] 已關閉 {closed} 個 stuck service worker target')
    return closed


def _start_chrome_from_wsl(cdp_url: str) -> None:
    """WSL 環境下自動啟動 Windows Chrome（帶 remote debugging）"""
    chrome_path = '/mnt/c/Program Files/Google/Chrome/Application/chrome.exe'
    if not os.path.exists(chrome_path):
        raise RuntimeError(
            f'找不到 Chrome：{chrome_path}\n'
            '請確認 Chrome 已安裝於 C:\\Program Files\\Google\\Chrome\\Application\\'
        )

    parsed = urlparse(cdp_url)
    port = parsed.port or 9222

    subprocess.Popen([
        chrome_path,
        f'--remote-debugging-port={port}',
        '--remote-debugging-address=0.0.0.0',
        '--user-data-dir=C:\\temp\\chrome-cdp-debug',
        '--no-first-run',
        '--no-default-browser-check',
    ])

    # 等待 Chrome 就緒（最多 10 秒）
    for _ in range(20):
        time.sleep(0.5)
        if _is_cdp_ready(cdp_url):
            return

    raise RuntimeError(f'Chrome 啟動超時，無法連線到 {cdp_url}')


def _new_configured_page(browser, install_toast_observer=True):
    """
    建立新的 browser context + page，並套用標準設定：
    - 視窗最大化（CDP `Browser.setWindowBounds windowState=maximized`）；
      CI 環境無 window manager 不支援，改用 explicit viewport 1920×1080
    - 注入 MutationObserver 自動關閉伺服器錯誤彈窗（`install_toast_observer=True` 時）
    回傳 (context, page)

    若 setup 過程任何步驟失敗，會關閉已建立的 context 再 raise，避免 Chrome 視窗洩漏。

    歷史記錄（2026-05-04 嘗試移除 / 改寫 observer 失敗）：
    - 完全移除 → 6 fail + 5 error（伺服器錯誤 popup 擋住操作）
    - 白名單（只關「伺服器錯誤」）→ 漏其他 popup
    - 黑名單（密碼錯誤/帳號不存在不關）→ JS 掃 DOM 慢 50-100ms 仍被 popup 擋
    結論：保留原始 aggressive observer 為**預設**，不弱化任何 test 的 popup 防護。

    需斷言 toast 可見的 test（如 RC test_login_wrong_password /
    test_login_wrong_username）改用 `@pytest.mark.no_toast_observer` marker：
    `page` fixture 偵測到該 marker 時傳 `install_toast_observer=False`，**完全不安裝**
    observer（而非弱化其邏輯）→ toast 不再被秒關，斷言確定性成立，不需 rerun 吸收。
    """
    if _is_ci():
        # CI 用 explicit viewport（headless 無 window manager 不支援 setWindowBounds maximize）
        context = browser.new_context(viewport={"width": 1920, "height": 1080})
    else:
        # 本地（Windows / WSL / Linux + CDP）：no_viewport + CDP maximize
        context = browser.new_context(no_viewport=True)

    try:
        page = context.new_page()

        if not _is_ci():
            cdp = context.new_cdp_session(page)
            window_id = cdp.send("Browser.getWindowForTarget")["windowId"]
            cdp.send("Browser.setWindowBounds", {
                "windowId": window_id,
                "bounds": {"windowState": "maximized"},
            })
            cdp.detach()

        if install_toast_observer:
            page.add_init_script("""
                new MutationObserver(() => {
                    // 自動關閉伺服器錯誤彈窗（RC 站特有）
                    const toastBtn = document.querySelector('button.toast-confirm-btn');
                    if (toastBtn && toastBtn.offsetParent !== null) toastBtn.click();
                }).observe(document.body, { childList: true, subtree: true });
            """)
    except BaseException:
        context.close()
        raise

    return context, page


@pytest.fixture(scope="session")
def browser(playwright: Playwright):
    if _is_ci():
        # CI（GitHub Actions / 等）：直接 launch Playwright 內建 chromium，無需 CDP / Windows Chrome
        # 預設 headless（CI 無顯示），可用 HEADLESS=false 環境變數覆寫做 debug
        headless = os.getenv("HEADLESS", "true").lower() == "true"
        browser = playwright.chromium.launch(headless=headless)
        yield browser
        browser.close()
    elif sys.platform == 'win32':
        # Windows：Playwright 直接啟動 Chrome
        headless = os.getenv("HEADLESS", "false").lower() == "true"
        browser = playwright.chromium.launch(channel="chrome", headless=headless)
        yield browser
        browser.close()
    elif _is_wsl():
        # WSL：自動啟動 Windows Chrome（若尚未開啟），再透過 CDP 連線
        cdp_url = os.getenv("CDP_URL", "http://127.0.0.1:9222")
        if not _is_cdp_ready(cdp_url):
            print(f'\n[WSL] Chrome 尚未啟動，自動開啟中... ({cdp_url})')
            _start_chrome_from_wsl(cdp_url)
        # Pre-flight：關閉 stuck SW target（patch 已於 pytest_configure 套好）
        _detach_stuck_service_workers(cdp_url)
        browser = playwright.chromium.connect_over_cdp(cdp_url)
        yield browser
        # 不關閉 browser，避免把 Windows Chrome 一起關掉
    else:
        # 純 Linux（非 CI）：透過 CDP 連線（需自行確保 Chrome 已啟動）
        cdp_url = os.getenv("CDP_URL", "http://localhost:9222")
        _detach_stuck_service_workers(cdp_url)
        browser = playwright.chromium.connect_over_cdp(cdp_url)
        yield browser


# -----------------------------------------------
# pytest hooks
# -----------------------------------------------
def pytest_configure(config):
    """
    pytest 進入點：在任何 fixture／Playwright 初始化之前，
    套用 Playwright driver patch（crBrowser.js 容忍 pre-existing SW target）。
    必須在此時 patch，因為 Node driver 一啟動就會 require crBrowser.js 並快取，
    改在 browser fixture 裡 patch 已經太晚。
    """
    _patch_playwright_crbrowser_sw_assert()


def pytest_addoption(parser):
    parser.addoption(
        "--site",
        action="store",
        default=None,
        help="指定測試站點，例如：--site=wlj",
    )


# -----------------------------------------------
# Fixtures
# -----------------------------------------------
@pytest.fixture(scope="session")
def site_config(request):
    """讀取站點設定（整個 session 共用）"""
    site_id = request.config.getoption("--site")
    return get_site_config(site_id)


@pytest.fixture(scope="function")
def page(browser, request):
    """
    [Smoke 用] 每個測試建立獨立 context，視窗最大化。
    測試後由 auto_logout_after_test 自動登出並關閉 context。

    標了 `@pytest.mark.no_toast_observer` 的 test 不安裝全域 toast auto-close
    observer（供需斷言 toast/錯誤彈窗可見的 test 使用，避免 observer 秒關 race）。
    """
    install_observer = request.node.get_closest_marker("no_toast_observer") is None
    context, pg = _new_configured_page(browser, install_toast_observer=install_observer)
    try:
        yield pg
    finally:
        context.close()


@pytest.fixture(scope="function")
def login_page(page: Page, site_config):
    """提供 LoginPage 實例"""
    LoginPage = get_login_page_class(site_config.site_id)
    return LoginPage(page, site_config.url)


@pytest.fixture(scope="function")
def logged_in_page(page: Page, site_config):
    """
    [Smoke 用] 已登入狀態的 fixture，每個測試獨立 context。
    測試需要登入後才能執行的功能時使用這個。
    """
    LoginPage = get_login_page_class(site_config.site_id)
    HomePage = get_home_page_class(site_config.site_id)

    login = LoginPage(page, site_config.url)
    login.goto_and_login(site_config.username, site_config.password)

    home = HomePage(page)
    # 先清彈窗（RC 公告 popup 為 server async 渲染，可能在 verify 過程中跳出遮住 avatar）
    home.dismiss_any_popups()
    home.verify_logged_in()

    return page


@pytest.fixture(scope="class")
def class_logged_in_page(browser, site_config):
    """
    [功能測試用] Class-scoped 已登入 page。
    一個 class 只登入一次，class 內所有測試共用同一個 session。
    適用於需要登入但不測試登入/登出流程的功能型測試。

    搭配 go_home fixture 使用，可在每個測試前回到首頁。
    """
    LoginPage = get_login_page_class(site_config.site_id)
    HomePage = get_home_page_class(site_config.site_id)

    context, pg = _new_configured_page(browser)
    try:
        login = LoginPage(pg, site_config.url)
        login.goto_and_login(site_config.username, site_config.password)

        home = HomePage(pg)
        # 先清彈窗（RC 公告 popup 為 server async 渲染，可能在 verify 過程中跳出遮住 avatar）
        home.dismiss_any_popups()
        home.verify_logged_in()
    except BaseException:
        context.close()
        raise

    try:
        yield pg
    finally:
        context.close()


@pytest.fixture(scope="function")
def go_home(class_logged_in_page, site_config):
    """
    [功能測試用] 每個測試前回到首頁並清理彈窗。
    必須搭配 class_logged_in_page 使用。

    用法：
        def test_something(self, class_logged_in_page, go_home):
            page = class_logged_in_page
            ...
    """
    from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
    pg = class_logged_in_page
    pg.goto(site_config.url)
    pg.wait_for_load_state("networkidle")
    # 頁面導覽時也可能出現 loading 動畫，等它消失
    try:
        pg.locator('img[alt="Loading"]').wait_for(state="hidden", timeout=5000)
    except PlaywrightTimeoutError:
        pass
    dismiss_server_error_if_present(pg)
    yield


# -----------------------------------------------
# 自動截圖：對所有使用 page 或 class_logged_in_page 的測試生效
# POM 方法透過 get_screenshotter(page) 取得，無需在測試中手動傳遞
# -----------------------------------------------
@pytest.fixture(autouse=True)
def auto_screenshot(request):
    """
    自動為每個測試建立 ScreenshotHelper 並 attach 到對應 page。
    POM 方法會自動偵測並使用，截圖存於 screenshots/<site_id>/<timestamp>/<test_name>/。
    測試結束後自動產生 README.md 操作流程說明。
    """
    # 取得測試 docstring 作為說明文字
    description = ""
    fn = getattr(request.node, "function", None)
    if fn and fn.__doc__:
        description = fn.__doc__.strip()

    site_id = "unknown"
    if 'site_config' in request.fixturenames:
        site_id = request.getfixturevalue('site_config').site_id

    # 依測試檔案路徑判斷分類：feature/ 下為 feature，其餘為 smoke
    test_path = str(request.fspath)
    test_category = "feature" if "/feature/" in test_path else "smoke"

    attached_pages = []
    helpers = []

    for fixture_name in ('page', 'class_logged_in_page', 'dashboard_page'):
        if fixture_name in request.fixturenames:
            pg = request.getfixturevalue(fixture_name)
            sh = ScreenshotHelper(pg, request.node.name, description, site_id=site_id, category=test_category)
            attach_screenshotter(pg, sh)
            attached_pages.append(pg)
            helpers.append(sh)

    yield

    # 測試結束：產生 README.md，再 detach
    for sh in helpers:
        sh.generate_report()
    for pg in attached_pages:
        detach_screenshotter(pg)


# -----------------------------------------------
# 每個 Smoke 測試結束後：嘗試登出
# 僅對使用 function-scoped page 的測試生效
# -----------------------------------------------
@pytest.fixture(autouse=True)
def auto_logout_after_test(request):
    yield
    if 'page' not in request.fixturenames:
        return  # 使用 class_logged_in_page 的測試略過，不登出
    try:
        pg = request.getfixturevalue('page')
        sc = request.getfixturevalue('site_config')
        HomePage = get_home_page_class(sc.site_id)
        home = HomePage(pg)
        if home.is_logged_in():
            home.logout()
    except Exception:
        pass  # 未登入或已登出，略過
