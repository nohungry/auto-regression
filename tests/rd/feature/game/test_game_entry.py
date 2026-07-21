"""
RD 前台遊戲進入測試 (狗狗娛樂城)
RD-GAME-001

使用 .env 的 SITE_RD_USERNAME 登入前台 → 點 navbar「電子」進 /Categories/slots →
hover 第一個 .card-item → 點 .play 按鈕 → 期望開新 tab 進入 launchLoading 頁
→ 驗 iframe + canvas mount。

與 RC / RE 差異：
- RD 點「電子」直接進 `/Categories/slots?gamePlatformId=1031`（預選平台），無 .game-type / .platform-list-bg 步驟
- RD 遊戲卡片為 `.card-item` + 內含 `.play` button（hover 顯示）
- RD 點 .play 開**新 tab** `/launchLoading?gameId=...&gameName=關老爺`，與 RC / RE 同 tab 載入不同
- 不做 spin / 注單紀錄等遊戲內互動（RD 站尚無 canvas mouse coord 校準資料）

⚠️ 已知 dev-rd regression（2026-05-11 觀察）：
launchLoading 頁載入後 body 為空、無 iframe、無 canvas — 遊戲後端未渲染。
與 RC `test_enter_and_spin` 同類型問題（CLAUDE.md「測試結果判讀」反例 5305 連線失敗）。
此 test 會以 RuntimeError fail，視為 **真實 regression 訊號**，不加 skip 掩蓋。
產品端遊戲後端修復後，test 會自動轉為 PASS。
"""

import re
import pytest
from playwright.sync_api import Page, expect
from pages.factory import get_login_page_class, get_home_page_class
from utils.dialog_helper import wait_loading_if_present, dismiss_dialog_mask_if_present
from utils.game_launch_helper import get_game_frame
from utils.screenshot_helper import get_screenshotter


LoginPage = get_login_page_class("rd")
HomePage = get_home_page_class("rd")

CATEGORY_NAV = "電子"


@pytest.mark.p1
@pytest.mark.rd
@pytest.mark.game
class TestGameEntry:
    """RD-GAME-001：前台遊戲進入流程"""

    def test_enter_game(self, page: Page, site_config):
        """RD-GAME-001：登入 → 電子 → 點第一個 game card 的 play → 新 tab 載入 → 驗 iframe + canvas"""
        sh = get_screenshotter(page)

        # ===== Phase 1: 登入 =====
        login = LoginPage(page, site_config.url)
        login.goto_and_login(site_config.username, site_config.password)
        home = HomePage(page)
        home.verify_login_success(site_config.username)
        home.dismiss_any_popups()
        dismiss_dialog_mask_if_present(page)
        if sh: sh.full_page("verify_登入成功")

        # ===== Phase 2: 進電子分類 =====
        home.click_nav_item(CATEGORY_NAV)
        expect(page).to_have_url(re.compile("Categories/slots"), timeout=8000)
        wait_loading_if_present(page)
        page.wait_for_timeout(2000)
        dismiss_dialog_mask_if_present(page)
        if sh: sh.full_page("verify_電子分類頁載入")

        # ===== Phase 3: 點第一個 card 的 .play 按鈕，期待開新 tab =====
        first_card = page.locator(".card-item").first
        expect(first_card).to_be_visible(timeout=10000)
        first_card.scroll_into_view_if_needed()
        first_card.hover()  # hover 顯示 .play 按鈕
        page.wait_for_timeout(500)

        play_btn = first_card.locator(".play").first
        if sh: sh.capture(play_btn, "click_第一個遊戲card_play按鈕")

        # 點擊 .play 預期開新 tab（/launchLoading?gameId=...）
        with page.context.expect_page(timeout=15000) as new_page_info:
            play_btn.click(force=True)
        new_page = new_page_info.value

        new_page.wait_for_load_state("domcontentloaded", timeout=20000)
        new_page.wait_for_timeout(3000)
        if sh:
            # 截圖前最後一張在原 page 上（new_page 不在 ScreenshotHelper 控管下）
            sh.full_page(f"verify_新tab已開_url{new_page.url[:80]}")

        # ===== Phase 4: 驗新 tab 內 iframe + canvas mount =====
        # 此步驟若 fail（找不到 canvas iframe）= dev-rd 遊戲後端 regression 訊號
        game_frame = get_game_frame(new_page, timeout=30000)
        new_page.wait_for_timeout(3000)

        canvas_count = game_frame.evaluate("() => document.querySelectorAll('canvas').length")
        assert canvas_count > 0, f"遊戲 iframe 內找不到 canvas（count={canvas_count}）"
