"""
語系切換輔助函式
- set_locale：注入語系 cookie，適用於 lt 站點
- switch_language_via_globe：globe icon UI 切換語系，適用於 rc/re 型站點

set_locale 適用於 lt 站點（見 .env SITE_LT_URL）的多語系測試
cookie 名稱：i18n_locale（2026-05-18 換版後改名，原 i18n_redirected_lt 已失效）
支援語系：tw（繁中）/ cn（簡中）/ en（英文）/ th（泰文）/ vn（越文）
"""

from urllib.parse import urlparse
from playwright.sync_api import Page

from utils.dialog_helper import (
    dismiss_announcement_popup_if_present,
    dismiss_server_error_if_present,
)


def set_locale(page: Page, base_url: str, locale: str = "tw") -> None:
    """
    在 page context 寫入語系 cookie，需在 goto() 前呼叫。

    用法：
        set_locale(page, site_config.url, "tw")
        page.goto(site_config.url)
    """
    domain = urlparse(base_url).hostname
    page.context.add_cookies([{
        "name": "i18n_locale",
        "value": locale,
        "domain": domain,
        "path": "/",
    }])


def switch_language_via_globe(page: Page, url: str, lang_name: str) -> None:
    """前往首頁 → dismiss 彈窗 → globe icon 切換語系（RC/RE 型站點 i18n 測試共用）"""
    page.goto(url, wait_until="networkidle")
    dismiss_server_error_if_present(page)
    dismiss_announcement_popup_if_present(page, timeout=3000)
    globe = page.locator("img[src*='global']")
    globe.scroll_into_view_if_needed()
    globe.click()
    lang_option = page.locator("p.whitespace-nowrap", has_text=lang_name).first
    lang_option.wait_for(state="visible", timeout=5000)
    lang_option.click()
    page.wait_for_load_state("networkidle")
    dismiss_server_error_if_present(page)
