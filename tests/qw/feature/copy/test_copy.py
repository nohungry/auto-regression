"""
QW 文案一致性驗證（LM來財娛樂城）
QW-TC-C01 ~ QW-TC-C02

驗證 QW 站「預設語系（繁體）」下的品牌/導覽文案資產（probe 2026-06-25）：
- 網站標題（預期「LM來財娛樂城」；⚠️ QW dev 實際誤掛「王老吉娛樂城」=RC 名 → xfail 守門）
- 頂部 nav 主分類顯示文字與順序（ul.nav-item li，繁體，含「首頁」與「優惠」）

只驗未登入公開頁可見的文案；多語系切換驗證見 tests/qw/feature/i18n/。

QW 多語系特性：以 LaiBetLanguage cookie 切換語系，預設繁體中文（zh）。
nav 文案與 KS（簡體）不同：QW 繁體（電子/真人/捕魚/棋牌/體育/彩票/鬥雞）。
"""

import pytest
from playwright.sync_api import Page, expect
from utils.screenshot_helper import get_screenshotter

# 頂部 nav 顯示文字（ul.nav-item li，繁體；probe 2026-06-25 確認）
# 含「首頁」和「優惠」兩個 <a href> 連結，與 KS 簡體不同
EXPECTED_NAV_LABELS = [
    "首頁", "電子", "真人", "捕魚", "棋牌", "體育", "彩票", "鬥雞", "優惠",
]


@pytest.mark.p2
@pytest.mark.qw
@pytest.mark.copy
class TestCopy:
    """QW 文案一致性驗證（未登入公開頁）"""

    @pytest.mark.xfail(
        strict=True,
        reason="QW dev 前端 <title> 誤掛「王老吉娛樂城」（RC 站名，疑似從 RC 模板複製未改）；"
               "正確應為「LM來財娛樂城」。產品修正 title 後此 xfail 會 XPASS 守門。",
    )
    def test_home_title(self, page: Page, site_config):
        """QW-TC-C01：首頁網站標題應為 QW 品牌名稱「LM來財娛樂城」

        斷言策略：
        - 驗 title 等於**正確品牌名**「LM來財娛樂城」（不綁 QW dev 當前誤值）
        - 截圖帶實際 title 文字供 review 判斷差異
        - 目前 QW dev title 誤掛「王老吉娛樂城」→ 本測試以 xfail(strict) 守門，
          產品端修正 title 後會 XPASS 提醒移除 xfail。

        注意：直接 goto 首頁（/），不透過 LoginPage.goto()（後者導向 /auth，
        title 可能不同）。
        """
        page.goto(site_config.url, wait_until="networkidle", timeout=60000)
        sh = get_screenshotter(page)
        actual_title = page.title()
        if sh: sh.full_page(f"verify_首頁title_{actual_title!r}")
        expect(page).to_have_title("LM來財娛樂城")

    def test_nav_labels(self, page: Page, site_config):
        """QW-TC-C02：頂部 nav 主分類顯示文字與順序正確（繁體）

        斷言策略：
        - 驗 ul.nav-item li 文字陣列與預期完全一致（含首頁/優惠）
        - 截圖帶實際 labels 供 review

        注意：nav 在首頁（/）；LoginPage.goto() 導向 /auth 頁故不含 nav-item。
        此 TC 直接 goto 首頁（不需登入即可驗 nav 文案）。
        """
        page.goto(site_config.url, wait_until="networkidle", timeout=60000)
        # dismiss popup 以確保截圖清晰（不影響 DOM text 取值）
        try:
            page.locator(".popup-close").first.wait_for(state="visible", timeout=8000)
            page.locator(".popup-close").first.click()
        except Exception:
            pass
        labels = page.locator("ul.nav-item li").evaluate_all(
            "els => els.map(li => (li.textContent || '').trim())"
        )
        sh = get_screenshotter(page)
        if sh: sh.full_page(f"verify_nav文案_{labels}")
        assert labels == EXPECTED_NAV_LABELS, (
            f"nav 文案不符，實際：{labels}，預期：{EXPECTED_NAV_LABELS}"
        )
