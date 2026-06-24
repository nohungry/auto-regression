"""
QW 首頁各區塊測試（LM來財娛樂城）
QW-HOME-001 ~ 004

驗證登入後首頁主要結構區塊（selector 來源：probe 2026-06-25）：
1. Banner carousel（.swiper，5 張輪播 slide）
2. 新聞跑馬燈（.bcast-desktop）
3. 遊戲 intro 區（div[class*="pt-[44px]"]）含分類 tab（.intro-tab）和提供商 tiles（.intro-platform）
4. 特色功能介紹區（div[class*="pt-[96px]"]）—快速存款轉帳、眾多遊戲種類等

與 navigation/wallet/announcement feature 區隔：只驗首頁 body 內容區塊呈現，
不點 nav、不驗餘額導航、不測公告彈窗。go_home 已 dismiss 進站公告。

QW 首頁結構（probe 2026-06-25）：
- .inner-scroll > .cs-wrapper（CS client service button）
- .inner-scroll > .main-page（主內容）
  - .mx-auto.w-full.overflow-hidden：Banner swiper
  - .bcast-desktop：新聞跑馬燈
  - div[pt-44px]：遊戲 intro（.intro-tab + .intro-platform）
  - div[pt-160px]：行動版 App 下載區（含 QR code）
  - div[pt-96px / pb-146px]：特色功能介紹
- .inner-scroll > footer

注意：QW 無 KS 的 .broadcast-bg/.hot-game-bg 等 class；使用 QW 自有的命名。
"""

import pytest
from playwright.sync_api import Page, expect
from utils.screenshot_helper import get_screenshotter


@pytest.mark.p1
@pytest.mark.qw
@pytest.mark.home
class TestHomePageSections:
    """QW-HOME-001 ~ 004：首頁主要區塊"""

    def test_banner_carousel(self, class_logged_in_page: Page, go_home):
        """QW-HOME-001：首頁 banner carousel（.swiper）可見且含 slide"""
        page = class_logged_in_page
        sh = get_screenshotter(page)
        # banner swiper 在 .main-page 的第一個子容器內
        swiper = page.locator(".swiper").first
        swiper.scroll_into_view_if_needed()
        if sh: sh.capture(swiper, "verify_banner_carousel")
        expect(swiper).to_be_visible()
        # 驗 slide 數量 > 0（probe 確認 5 張）
        slides = swiper.locator(".swiper-slide")
        slide_count = slides.count()
        if sh: sh.full_page(f"verify_banner_slide_count{slide_count}")
        assert slide_count > 0, f"banner carousel 應有 slide，實際 {slide_count}"

    def test_broadcast_marquee(self, class_logged_in_page: Page, go_home):
        """QW-HOME-002：首頁新聞跑馬燈（.bcast-desktop）可見且含文字"""
        page = class_logged_in_page
        sh = get_screenshotter(page)
        bcast = page.locator(".bcast-desktop").first
        bcast.scroll_into_view_if_needed()
        if sh: sh.capture(bcast, "verify_新聞跑馬燈")
        expect(bcast).to_be_visible()
        # bcast-inner 含跑馬燈文字（不驗特定文案，僅確認非空）
        inner = bcast.locator(".bcast-inner").first
        inner_text = inner.inner_text()
        if sh: sh.full_page(f"verify_跑馬燈文字非空_len{len(inner_text)}")
        assert len(inner_text.strip()) > 0, "跑馬燈文字不應為空"

    def test_game_intro_section(self, class_logged_in_page: Page, go_home):
        """QW-HOME-003：遊戲 intro 區（pt-[44px]）可見且含分類 tab 和提供商 tiles

        斷言策略：
        - div[class*="pt-[44px]"] 可見（遊戲 intro 容器）
        - .intro-tab 分類 tab 數量 > 0（probe 確認 6 個：電子/真人/捕魚/棋牌/體育/彩票）
        - .intro-platform 提供商 tiles 數量 > 0（電子 tab 下有多個 provider）
        不驗文案（多語系）；不點 tab（navigation test 已涵蓋）。
        """
        page = class_logged_in_page
        sh = get_screenshotter(page)
        # 用 attribute substring selector，Playwright CSS selector 不支援 arbitrary Tailwind value 直接比對
        # 改用 has-text 或 page.evaluate 定位
        section = page.locator("css=div.main-page > div:nth-child(3)").first
        section.scroll_into_view_if_needed()
        if sh: sh.capture(section, "verify_遊戲intro區")
        expect(section).to_be_visible()

        # 驗 intro tab 數量
        tabs = page.locator(".intro-tab")
        tab_count = tabs.count()
        if sh: sh.full_page(f"verify_intro_tab_count{tab_count}")
        assert tab_count > 0, f".intro-tab 分類 tab 不應為 0，實際：{tab_count}"

        # 驗 intro platform tiles
        platforms = page.locator(".intro-platform")
        platform_count = platforms.count()
        if sh: sh.capture(platforms.first, f"verify_intro_platform_count{platform_count}")
        assert platform_count > 0, f".intro-platform tiles 不應為 0，實際：{platform_count}"

    def test_feature_section(self, class_logged_in_page: Page, go_home):
        """QW-HOME-004：特色功能介紹區（pt-[96px]）可見

        斷言策略：
        - .main-page 內第 5 個子容器（pt-96px / pb-146px）可見
        - 該區塊含 img（圖示）> 0
        不驗文案（多語系）。
        """
        page = class_logged_in_page
        sh = get_screenshotter(page)
        # 用 nth-child(5)（0-indexed 對應第 5 子節點：pb-146px / pt-96px 特色區）
        section = page.locator("css=div.main-page > div:nth-child(5)").first
        section.scroll_into_view_if_needed()
        if sh: sh.capture(section, "verify_特色功能介紹區")
        expect(section).to_be_visible()
        # 確認該 section 有圖片
        imgs = section.locator("img")
        img_count = imgs.count()
        if sh: sh.full_page(f"verify_特色區圖片_count{img_count}")
        assert img_count > 0, f"特色功能介紹區圖片不應為 0，實際：{img_count}"
