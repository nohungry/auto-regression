"""
DRC 文案一致性驗證

與 DLT `tests/dlt/feature/copy/test_copy.py` 意圖對齊，但 DRC 公開頁結構與 DLT 差異極大：
- DRC 預設 nav 語系為英文（Live Casino / Slots / Fishing），非繁中
- DRC 公開頁無 copyright footer、無客服入口、無登入頁獨立 placeholder 欄位
- DRC 廳館名稱（T9真人/RC真人/DG真人/MT真人/歐博）為固定品牌中文，不隨語系變動

因此本檔只驗證 DRC 站確實穩定的文案資產：
- 網站標題
- 主分類 href 順序（語系無關）
- 廳館卡片順序與中文名稱
"""

import pytest
from playwright.sync_api import Page, expect
from pages.drc.home_page import HomePage
from pages.drc.login_page import LoginPage
from utils.screenshot_helper import get_screenshotter


@pytest.mark.p1
@pytest.mark.copy
class TestCopy:
    """DRC 文案一致性驗證"""

    def test_home_title(self, page: Page, site_config):
        """首頁網站標題為「王老吉娛樂城」"""
        login = LoginPage(page, site_config.url)
        login.goto()
        expect(page).to_have_title("王老吉娛樂城")

    def test_home_category_order(self, page: Page, site_config):
        """首頁主分類 href 順序：casino → slots → fishing（語系無關）"""
        login = LoginPage(page, site_config.url)
        login.goto()
        hrefs = page.locator('a[href*="/Categories/"]').evaluate_all(
            """links => links.map(a => a.getAttribute('href'))"""
        )
        # 取前 3 個主分類，過濾掉 hash-only fragment
        main = [h for h in hrefs if "/Categories/" in h][:3]
        assert main == [
            "/Categories/casino#gameListSection",
            "/Categories/slots#gameListSection",
            "/Categories/fishing#gameListSection",
        ], f"主分類順序不符，實際：{main}"

    def test_casino_halls_order(self, class_logged_in_page: Page, go_home):
        """真人頁廳館順序固定為 T9真人 / RC真人 / DG真人 / MT真人 / 歐博"""
        page = class_logged_in_page
        home = HomePage(page)
        home.click_nav_item("真人")

        # 取得所有廳館卡片標題，`p:not(.text-black)` 排除隱藏 sidebar 節點
        hall_texts = page.locator("p:not(.text-black)").evaluate_all(
            """ps => ps
                .map(p => (p.textContent || '').trim())
                .filter(t => /^(T9真人|RC真人|DG真人|MT真人|歐博)$/.test(t))"""
        )
        # 保留出現順序（DOM 順序即顯示順序），去除連續重複
        deduped = []
        for t in hall_texts:
            if not deduped or deduped[-1] != t:
                deduped.append(t)

        assert deduped[:5] == ["T9真人", "RC真人", "DG真人", "MT真人", "歐博"], \
            f"廳館順序不符，實際：{deduped}"
        sh = get_screenshotter(page)
        if sh: sh.full_page("verify_廳館順序")
