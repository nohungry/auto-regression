"""
RF 文案一致性驗證（金爺娛樂城）
RF-TC-C01 ~ RF-TC-C03

驗證 RF 站「預設語系（繁體中文）」下的品牌/導覽文案資產（probe 2026-06-17）：
- RF-TC-C01：首頁 <title> 為品牌名稱（金爺娛樂城）
- RF-TC-C02：nav.menu_nav 主分類顯示文字與順序正確（繁中）
- RF-TC-C03：meta[name=description] 含品牌關鍵字（金爺娛樂城 / 在線娛樂）

只驗未登入公開頁可見的文案；語言切換後的文案變化見 tests/rf/feature/i18n/。

probe 2026-06-17：
- title = "金爺娛樂城"（無 slogan suffix，不同於 lg/ks 的「- 領先的在線娛樂遊戲體驗」格式）
- nav 繁中：[首頁, 真人, 電子, 捕魚]（4 個，較 lg/ks 精簡）
- meta description 含「金爺娛樂城提供全面的在線娛樂體驗…」品牌描述
"""

import pytest
from playwright.sync_api import Page, expect
from pages.factory import get_login_page_class
from utils.screenshot_helper import get_screenshotter


LoginPage = get_login_page_class("rf")

# 頂部 nav 顯示文字（nav.menu_nav a + button，繁體中文預設語系）
EXPECTED_NAV_LABELS = ["首頁", "真人", "電子", "捕魚"]

# meta description 必須包含的品牌關鍵字
META_DESC_KEYWORDS = ["金爺娛樂城", "在線娛樂"]


@pytest.mark.p2
@pytest.mark.rf
@pytest.mark.copy
class TestCopy:
    """RF 文案一致性驗證（未登入公開頁，繁體中文預設語系）"""

    def test_home_title(self, page: Page, site_config):
        """RF-TC-C01：首頁 <title> 為「金爺娛樂城」

        斷言策略：
        - 只驗 title 等於品牌名稱字串，不含 slogan（probe 確認 RF title 無 slogan suffix）
        - 若 RF 後續調整 title 格式，此 test 會明確失敗提示變動
        """
        LoginPage(page, site_config.url).goto()
        sh = get_screenshotter(page)
        if sh:
            sh.full_page(f"verify_首頁title_{page.title()}")
        expect(page).to_have_title("金爺娛樂城")

    def test_nav_labels(self, page: Page, site_config):
        """RF-TC-C02：nav.menu_nav 主分類文字與順序正確（繁中）

        斷言策略：
        - 驗整個 nav 的 a + button 文字列表順序（首頁/真人/電子/捕魚）
        - 用 evaluate 取所有 textContent，與 EXPECTED_NAV_LABELS 完整比對
        - 若項目新增/刪除/改名/換序，此 test 明確失敗
        """
        LoginPage(page, site_config.url).goto()
        labels = page.evaluate("""
        () => Array.from(document.querySelectorAll('nav.menu_nav a, nav.menu_nav button'))
            .map(e => (e.textContent || '').trim()).filter(t => t)
        """)
        sh = get_screenshotter(page)
        nav = page.locator("nav.menu_nav")
        nav.scroll_into_view_if_needed()
        if sh:
            sh.capture(nav, f"verify_nav文案_{labels}")
        assert labels == EXPECTED_NAV_LABELS, (
            f"nav 文案不符（繁中），預期={EXPECTED_NAV_LABELS}，實際={labels}"
        )

    def test_meta_description_keywords(self, page: Page, site_config):
        """RF-TC-C03：meta[name=description] 含品牌關鍵字（無漏翻譯 raw key）

        斷言策略：
        - 驗 meta description 非空
        - 驗 description 含「金爺娛樂城」（品牌一致性）及「在線娛樂」（服務描述）
        - 不驗完整文字，避免文案微調導致 test 脆弱
        - 驗無 i18n raw key 殘留（如 {{ ... }} 或 common.xxx 格式）
        """
        LoginPage(page, site_config.url).goto()
        meta_desc = page.evaluate("""
        () => {
            const el = document.querySelector('meta[name="description"]');
            return el ? el.getAttribute('content') || '' : '';
        }
        """)
        sh = get_screenshotter(page)
        if sh:
            sh.full_page("verify_meta_description關鍵字")
        assert meta_desc, "meta[name=description] 為空或不存在"
        for keyword in META_DESC_KEYWORDS:
            assert keyword in meta_desc, (
                f"meta description 缺少品牌關鍵字 {keyword!r}，"
                f"實際 description={meta_desc!r}"
            )
        # 確認無 i18n raw key 殘留（{{ 或 common.）
        assert "{{" not in meta_desc, (
            f"meta description 疑似含 i18n raw key：{meta_desc!r}"
        )
        assert "common." not in meta_desc, (
            f"meta description 疑似含 i18n raw key（common.prefix）：{meta_desc!r}"
        )
