"""
KS 首頁各區塊測試（Super9娛樂城）

驗證登入後首頁主要結構區塊（selector 來源：selector-explorer probe 2026-06-08）：
1. 新聞跑馬燈（broadcast bar）
2. Recommended 分類 tiles（6 個：Slots/Casino/Sports/Fishing/mini game/Lottery）
3. Hot Game 熱門遊戲 section（遊戲卡 swiper）
4. Winner / Jackpot 即時展示區

與 navigation/wallet/announcement feature 區隔：只驗首頁 body 內容區塊呈現，
不點 nav、不驗餘額導航、不測公告彈窗。go_home 已 dismiss 進站公告。

KS 简体/英文混合主題（nav 英文、遊戲標題中文）。dev 環境 .dialog-mask fade transition
殘留（opacity:0），本檔只做 visibility/scroll 不點擊，不受殘留 mask 影響。
Hot Game 遊戲 grid 延遲渲染，卡片數驗證前 wait attached。
"""

import pytest
from playwright.sync_api import Page, expect
from utils.screenshot_helper import get_screenshotter


@pytest.mark.p1
@pytest.mark.ks
@pytest.mark.home
class TestHomePageSections:
    """KS-HOME-001 ~ 004：首頁主要區塊"""

    def test_broadcast_marquee(self, class_logged_in_page: Page, go_home):
        """KS-HOME-001：首頁新聞跑馬燈（broadcast bar）可見"""
        page = class_logged_in_page
        sh = get_screenshotter(page)
        broadcast = page.locator(".broadcast-bg").first
        broadcast.scroll_into_view_if_needed()
        if sh: sh.capture(broadcast, "verify_新聞跑馬燈")
        expect(broadcast).to_be_visible()

    def test_recommended_tiles(self, class_logged_in_page: Page, go_home):
        """KS-HOME-002：Recommended 分類 tiles 顯示 6 個入口"""
        page = class_logged_in_page
        sh = get_screenshotter(page)
        container = page.locator(".min-h-0.flex-1.space-y-2.overflow-y-auto").first
        container.scroll_into_view_if_needed()
        if sh: sh.capture(container, "verify_Recommended_tiles")
        expect(container).to_be_visible()
        # 結構性斷言 6 個 tile（不綁標題文案：KS locale 在 cn(推荐游戏)/en(Recommended)
        # 間變動，且 .text-[20px].text-main 該 class 非唯一命中多個，綁文案脆弱）
        tiles = container.locator(".cursor-pointer")
        assert tiles.count() == 6, f"Recommended tiles 應為 6 個，實際 {tiles.count()}"

    def test_hot_game_section(self, class_logged_in_page: Page, go_home):
        """KS-HOME-003：Hot Game 熱門遊戲 section 含遊戲卡"""
        page = class_logged_in_page
        sh = get_screenshotter(page)
        section = page.locator(".hot-game-bg").first
        section.scroll_into_view_if_needed()
        page.wait_for_timeout(500)
        if sh: sh.full_page("verify_HotGame_全頁")
        expect(section).to_be_visible()
        cards = section.locator(".img-hover.cursor-pointer")
        cards.first.wait_for(state="attached", timeout=15000)
        count = cards.count()
        assert count > 0, "Hot Game 遊戲卡不應為 0"
        if sh: sh.capture(cards.first, f"verify_HotGame遊戲卡_count{count}")

    def test_winner_jackpot_section(self, class_logged_in_page: Page, go_home):
        """KS-HOME-004：Winner / Jackpot 即時展示區可見"""
        page = class_logged_in_page
        sh = get_screenshotter(page)
        section = page.locator(".max-h-\\[734px\\]").first
        section.scroll_into_view_if_needed()
        if sh: sh.capture(section, "verify_Winner_Jackpot區")
        expect(section).to_be_visible()
