"""
RD 文案一致性驗證（職責：預設語系下的品牌/結構文案）— 狗狗娛樂城

本檔只驗證 RD 站「不隨語系變動」或「預設語系」下的文案資產：
- 網站標題
- 主分類 href 順序（語系無關）
- 頁尾品牌字串（dlgbet88.com）

多語系切換後的文案驗證請見 `tests/rd/feature/i18n/`（home / login / sidebar locale）。

與 RC `tests/rc/feature/copy/test_copy.py` 意圖對齊，但 RD 結構差異：
- 主分類 6 個（slots / casino / fishing / sport / lottery / cockfighting；RC 只有 5 個）
- RD 真人頁無顯式廳館名稱卡片（皆為遊戲圖卡）→ 不測廳館順序
- RD 頁尾有公司資訊段落（dlgbet88.com / Decordetals OÜ）+ copyright
"""

import pytest
from playwright.sync_api import Page, expect
from pages.factory import get_login_page_class
from utils.screenshot_helper import get_screenshotter


LoginPage = get_login_page_class("rd")


@pytest.mark.p2
@pytest.mark.rd
@pytest.mark.copy
class TestCopy:
    """RD-COPY-001 ~ 003：文案一致性"""

    def test_home_title(self, page: Page, site_config):
        """RD-COPY-001：首頁網站標題為「狗狗娛樂城」"""
        login = LoginPage(page, site_config.url)
        login.goto()
        sh = get_screenshotter(page)
        if sh: sh.full_page("verify_首頁title檢測")
        expect(page).to_have_title("狗狗娛樂城")

    def test_home_category_order(self, page: Page, site_config):
        """RD-COPY-002：首頁主分類 href 順序：slots → casino → fishing → sport → lottery → cockfighting

        RD 6 分類順序為品牌設計，語系切換不影響 URL（URL 為 en，content 為 i18n 文案）。
        """
        login = LoginPage(page, site_config.url)
        login.goto()
        hrefs = page.locator('a[href*="/Categories/"]').evaluate_all(
            """links => links.map(a => a.getAttribute('href'))"""
        )
        # 取前 6 個主分類，過濾掉帶 query string 的子分類連結
        main = [h for h in hrefs if "/Categories/" in h and "?" not in h]
        # 去重保序
        seen = []
        for h in main:
            if h not in seen:
                seen.append(h)
        sh = get_screenshotter(page)
        if sh: sh.full_page(f"verify_主分類順序檢測_{seen[:6]}")
        assert seen[:6] == [
            "/Categories/slots",
            "/Categories/casino",
            "/Categories/fishing",
            "/Categories/sport",
            "/Categories/lottery",
            "/Categories/cockfighting",
        ], f"主分類順序不符，實際：{seen}"

    def test_footer_brand_text(self, page: Page, site_config):
        """RD-COPY-003：頁尾顯示品牌字串「dlgbet88.com」與 copyright

        斷言策略：直接以 body.to_contain_text 驗證頁尾品牌字串存在，
        不依賴元素 visibility（小 viewport 下頁尾段落可能 CSS 折疊但 DOM 中存在）。
        年份 / 公司註冊資訊細節不寫死，避免一年一改。
        """
        login = LoginPage(page, site_config.url)
        login.goto()

        sh = get_screenshotter(page)

        # 先存全頁截圖當證據（assert 前先寫，以防 fail 拿不到圖）
        # 滾到頁底以便截圖看到頁尾
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        page.wait_for_timeout(500)
        if sh: sh.full_page("verify_頁尾品牌_dlgbet88_All_rights_reserved_檢測")

        body = page.locator("body")
        # 品牌字串
        expect(body).to_contain_text("dlgbet88.com")
        # Copyright 字串
        expect(body).to_contain_text("All rights reserved")
