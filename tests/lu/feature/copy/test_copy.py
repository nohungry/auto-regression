"""
LU 文案一致性驗證（Dlgbet）
LU-TC-C01 ~ LU-TC-C02

驗證 LU 站「預設語系」下的品牌/導覽文案資產（probe 2026-06-07）：
- 網站標題（品牌「Dlgbet」，英文）
- 主分類 href 順序（語系無關）

LU 與 LG/KS 結構差異：**無 ul.nav-item**，nav 文字混入 banner 雜訊（如「Drive into
our...」），故文案驗證改用穩定的 category href 順序，不驗 nav 顯示文字。
多語系切換驗證見 tests/lu/feature/i18n/。
"""

import pytest
from playwright.sync_api import Page, expect
from pages.factory import get_login_page_class
from utils.screenshot_helper import get_screenshotter


LoginPage = get_login_page_class("lu")

# 主分類 href 順序（去重、取 primary，不含 gamePlatformId / View-all 變體）
EXPECTED_CATEGORY_ORDER = [
    "/Categories/slots",
    "/Categories/casino",
    "/Categories/fishing",
    "/Categories/sport",
    "/Categories/poker",
    "/Categories/lottery",
]


@pytest.mark.p2
@pytest.mark.lu
@pytest.mark.copy
class TestCopy:
    """LU 文案一致性驗證（未登入公開頁）"""

    def test_home_title(self, page: Page, site_config):
        """LU-TC-C01：首頁網站標題為品牌「Dlgbet」"""
        LoginPage(page, site_config.url).goto()
        sh = get_screenshotter(page)
        if sh: sh.full_page(f"verify_首頁title_{page.title()}")
        expect(page).to_have_title("Dlgbet")

    def test_category_order(self, page: Page, site_config):
        """LU-TC-C02：主分類 href 順序：slots→casino→fishing→sport→poker→lottery"""
        LoginPage(page, site_config.url).goto()
        hrefs = page.locator("a[href*='/Categories/']").evaluate_all(
            "els => els.map(a => a.getAttribute('href'))"
        )
        # 去重取 primary path（去 query/hash），保留 DOM 順序
        primary = []
        for h in hrefs:
            path = (h or "").split("?")[0].split("#")[0]
            if path.startswith("/Categories/") and path not in primary:
                primary.append(path)
        main = primary[:6]
        sh = get_screenshotter(page)
        if sh: sh.full_page(f"verify_主分類順序_{main}")
        assert main == EXPECTED_CATEGORY_ORDER, f"主分類順序不符，實際：{main}"
