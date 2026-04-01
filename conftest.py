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


def _new_configured_page(browser):
    """
    建立新的 browser context + page，並套用標準設定：
    - 視窗最大化（CDP）
    - 注入 MutationObserver 自動關閉伺服器錯誤彈窗
    回傳 (context, page)
    """
    context = browser.new_context(no_viewport=True)
    page = context.new_page()

    cdp = context.new_cdp_session(page)
    window_id = cdp.send("Browser.getWindowForTarget")["windowId"]
    cdp.send("Browser.setWindowBounds", {
        "windowId": window_id,
        "bounds": {"windowState": "maximized"},
    })
    cdp.detach()

    page.add_init_script("""
        new MutationObserver(() => {
            const btn = document.querySelector('button.toast-confirm-btn');
            if (btn && btn.offsetParent !== null) btn.click();
        }).observe(document.body, { childList: true, subtree: true });
    """)

    return context, page


@pytest.fixture(scope="session")
def browser(playwright: Playwright):
    if sys.platform == 'win32':
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
        browser = playwright.chromium.connect_over_cdp(cdp_url)
        yield browser
        # 不關閉 browser，避免把 Windows Chrome 一起關掉
    else:
        # 純 Linux：透過 CDP 連線（需自行確保 Chrome 已啟動）
        cdp_url = os.getenv("CDP_URL", "http://localhost:9222")
        browser = playwright.chromium.connect_over_cdp(cdp_url)
        yield browser


# -----------------------------------------------
# 新增 --site 命令列參數
# -----------------------------------------------
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
def page(browser):
    """
    [Smoke 用] 每個測試建立獨立 context，視窗最大化。
    測試後由 auto_logout_after_test 自動登出並關閉 context。
    """
    context, pg = _new_configured_page(browser)
    yield pg
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
    home.verify_login_success(site_config.username)
    home.dismiss_any_popups()

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

    login = LoginPage(pg, site_config.url)
    login.goto_and_login(site_config.username, site_config.password)

    home = HomePage(pg)
    home.verify_login_success(site_config.username)
    home.dismiss_any_popups()

    yield pg
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

    attached_pages = []
    helpers = []

    for fixture_name in ('page', 'class_logged_in_page'):
        if fixture_name in request.fixturenames:
            pg = request.getfixturevalue(fixture_name)
            sh = ScreenshotHelper(pg, request.node.name, description, site_id=site_id)
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
