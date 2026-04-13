"""
語系 Cookie 輔助函式
適用於 lt 站點（見 .env SITE_LT_URL）的多語系測試
cookie 名稱：i18n_redirected_lt
支援語系：tw（繁中）/ cn（簡中）/ en（英文）/ th（泰文）/ vn（越文）
"""

from urllib.parse import urlparse
from playwright.sync_api import Page


def set_locale(page: Page, base_url: str, locale: str = "tw") -> None:
    """
    在 page context 寫入語系 cookie，需在 goto() 前呼叫。

    用法：
        set_locale(page, site_config.url, "tw")
        page.goto(site_config.url)
    """
    domain = urlparse(base_url).hostname
    page.context.add_cookies([{
        "name": "i18n_redirected_lt",
        "value": locale,
        "domain": domain,
        "path": "/",
    }])
