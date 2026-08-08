"""
LT 前台遊戲進入測試（desktop 版，2026-06-27 rewrite）
LT-GAME-001

2026-05-18 desktop 換版後遊戲入口流程改變（probe 2026-06-27 確認）：
- 舊 `.cat-btn` 分類入口（電子→T9電子→關老爺）已消失；首頁改為遊戲卡 grid（83 張，
  `.grid > .relative.cursor-pointer`）+ 3 個 swipe sections（來財獨家/爆分精選/活動專區）。
- **遊戲改「同分頁原地啟動」**（非舊版新分頁）：點遊戲卡 → 同頁載入遊戲 wrapper
  （2 個 iframe + 「回到大廳」按鈕），URL 維持 `/`。
- 「回到大廳」(`p.tip-single` 文字) 返回首頁。

職責定位（見 docs：網站優先於遊戲）：本測試驗**平台職責 = 遊戲能啟動 + 能返回大廳**，
不驗第三方遊戲內 spin/下注（舊版 canvas 座標 CDP 點擊脆弱且屬 provider 品質，已移除）。
"""

import pytest
from playwright.sync_api import Page, expect
from pages.factory import get_login_page_class, get_home_page_class
from utils.screenshot_helper import get_screenshotter


LoginPage = get_login_page_class("lt")
HomePage = get_home_page_class("lt")

GAME_CARD = ".grid > .relative.cursor-pointer"
BACK_TO_LOBBY = "回到大廳"  # 遊戲 wrapper 內返回鈕（tw locale；LT i18n 目前固定繁中）


@pytest.mark.p1
@pytest.mark.lt
@pytest.mark.game
class TestGameEntry:
    """LT-GAME-001：前台遊戲啟動與返回大廳（平台職責）"""

    def test_game_launch_and_return(self, page: Page, site_config):
        """登入 → 點首頁遊戲卡 → 遊戲原地啟動（回到大廳出現）→ 回到大廳 → 返回首頁"""
        sh = get_screenshotter(page)

        login = LoginPage(page, site_config.url)
        login.goto_and_login(site_config.username, site_config.password)
        home = HomePage(page)
        home.verify_login_success(site_config.username)

        # 1) 首頁遊戲卡存在
        cards = page.locator(GAME_CARD)
        first_card = cards.first
        first_card.scroll_into_view_if_needed()
        expect(first_card).to_be_visible(timeout=15000)
        if sh: sh.capture(first_card, "verify_首頁遊戲卡")

        # 2) 點遊戲卡 → 遊戲同分頁啟動
        if sh: sh.capture(first_card, "click_遊戲卡")
        first_card.click(force=True)

        # 3) 驗遊戲啟動：wrapper 的「回到大廳」按鈕出現（遊戲載入慢，timeout 放寬）
        back_btn = page.get_by_text(BACK_TO_LOBBY, exact=True).first
        back_btn.wait_for(state="visible", timeout=30000)
        # 遊戲內容載入於 iframe（平台啟動成功信號）
        expect(page.locator("iframe").first).to_be_attached(timeout=10000)
        if sh: sh.full_page("verify_遊戲已啟動_回到大廳出現")

        # 4) 回到大廳 → 返回首頁（遊戲卡再現）
        back_btn.click(force=True)
        expect(cards.first).to_be_visible(timeout=15000)
        if sh: sh.full_page("verify_返回首頁_遊戲卡再現")
