"""
RE 文案一致性驗證 (BeWin) — 預設語系下的品牌/結構文案

本檔只驗證 RE 站「不隨語系變動」或「預設語系」下的文案資產：
- 網站標題（"BeWin"）
- 主分類 href 順序（語系無關）
- 廳館卡片順序與中文名稱（品牌固定中文）

多語系切換後的文案驗證請見 `tests/re/feature/i18n/`。

與 RC `tests/rc/feature/copy/test_copy.py` 意圖對齊；RE 共用平台 DOM
與廳館品牌（T9真人/RC真人/DG真人/MT真人/歐博），差異僅在站台 title。
"""

import pytest
from playwright.sync_api import Page, expect
from pages.re.home_page import HomePage
from pages.re.login_page import LoginPage
from utils.screenshot_helper import get_screenshotter


@pytest.mark.p2
@pytest.mark.re
@pytest.mark.copy
class TestCopy:
    """RE 文案一致性驗證"""

    def test_home_title(self, page: Page, site_config):
        """首頁網站標題為「BeWin」"""
        login = LoginPage(page, site_config.url)
        login.goto()
        sh = get_screenshotter(page)
        if sh: sh.full_page(f"verify_首頁title檢測_{page.title()}")
        expect(page).to_have_title("BeWin")

    def test_home_category_order(self, page: Page, site_config):
        """首頁主分類 href 順序：casino → slots → fishing（語系無關）

        RE 額外有體育/鬥雞 nav，但 /Categories/ 主分類前 3 個應仍為 casino/slots/fishing。
        RE 的 href 不帶 #gameListSection hash（與 RC 不同）。
        """
        login = LoginPage(page, site_config.url)
        login.goto()
        hrefs = page.locator('a[href*="/Categories/"]').evaluate_all(
            """links => links.map(a => a.getAttribute('href'))"""
        )
        # 取前 3 個主分類，過濾掉 hash-only fragment
        main = [h for h in hrefs if "/Categories/" in h][:3]
        sh = get_screenshotter(page)
        if sh: sh.full_page(f"verify_主分類順序檢測_{main}")
        assert main == [
            "/Categories/casino",
            "/Categories/slots",
            "/Categories/fishing",
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

        sh = get_screenshotter(page)
        if sh: sh.full_page(f"verify_廳館順序檢測_{deduped[:5]}")
        assert deduped[:5] == ["T9真人", "RC真人", "DG真人", "MT真人", "歐博"], \
            f"廳館順序不符，實際：{deduped}"
