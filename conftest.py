"""
pytest 全域設定
- 讀取 --site 參數
- 提供 site_config / page / logged_in_page fixture
- 每個測試結束後自動登出

執行環境自動偵測：
- Windows：Playwright 直接啟動 Chrome（無需手動開瀏覽器）
- WSL/Linux：透過 CDP 連線到已開啟的 Windows Chrome（需設定 CDP_URL）
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
from pages.login_page import LoginPage
from pages.home_page import HomePage


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


@pytest.fixture(scope="function")
def page(browser):
    """每個測試建立獨立 context，視窗最大化"""
    context = browser.new_context(no_viewport=True)
    page = context.new_page()
    # 透過 CDP 指令將視窗最大化
    cdp = context.new_cdp_session(page)
    window_id = cdp.send("Browser.getWindowForTarget")["windowId"]
    cdp.send("Browser.setWindowBounds", {
        "windowId": window_id,
        "bounds": {"windowState": "maximized"},
    })
    cdp.detach()
    # 注入 MutationObserver：偵測到「伺服器錯誤」彈窗時自動點確定
    page.add_init_script("""
        new MutationObserver(() => {
            const btn = document.querySelector('button.toast-confirm-btn');
            if (btn && btn.offsetParent !== null) btn.click();
        }).observe(document.body, { childList: true, subtree: true });
    """)
    yield page
    context.close()


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
# 每個測試結束後：嘗試登出，再等 3 秒
# -----------------------------------------------
@pytest.fixture(autouse=True)
def auto_logout_after_test(page: Page):
    yield
    try:
        home = HomePage(page)
        # 如果頭像存在代表還在登入狀態，執行登出
        if home.avatar.is_visible(timeout=2000):
            home.logout()
    except Exception:
        pass  # 未登入或已登出，略過
    time.sleep(3)


# -----------------------------------------------
# Fixtures
# -----------------------------------------------
@pytest.fixture(scope="session")
def site_config(request):
    """讀取站點設定（整個 session 共用）"""
    site_id = request.config.getoption("--site")
    return get_site_config(site_id)


@pytest.fixture(scope="function")
def login_page(page: Page, site_config):
    """提供 LoginPage 實例"""
    return LoginPage(page, site_config.url)


@pytest.fixture(scope="function")
def logged_in_page(page: Page, site_config):
    """
    已登入狀態的 fixture
    測試需要登入後才能執行的功能時使用這個
    """
    login = LoginPage(page, site_config.url)
    login.goto_and_login(site_config.username, site_config.password)

    home = HomePage(page)
    home.verify_login_success(site_config.username)
    home.dismiss_any_popups()

    return page
