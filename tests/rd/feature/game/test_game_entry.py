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
[2026-06-12 更新] 此 dev 遊戲後端問題（rc/re/rd 同款）長期紅燈，依團隊決定改以
@pytest.mark.skip 暫時跳過，避免干擾套件；遊戲後端修復後移除 skip，test 即恢復為
regression 守門（屆時會以 RuntimeError fail 反映實況、修好後 PASS）。
"""

import re
import time
import pytest
from playwright.sync_api import Page, Frame, expect
from pages.factory import get_login_page_class, get_home_page_class
from utils.dialog_helper import wait_loading_if_present, dismiss_dialog_mask_if_present
from utils.screenshot_helper import get_screenshotter


LoginPage = get_login_page_class("rd")
HomePage = get_home_page_class("rd")

CATEGORY_NAV = "電子"


def _get_game_frame(page: Page, timeout: int = 30000) -> Frame:
    """等待包含 canvas 的遊戲 iframe 出現（與 RC / RE 同 helper）"""
    deadline = time.time() + timeout / 1000
    while time.time() < deadline:
        for frame in page.frames:
            if frame == page.main_frame:
                continue
            if frame.url and frame.url != "about:blank":
                try:
                    if frame.query_selector("canvas"):
                        return frame
                except Exception:
                    pass
        page.wait_for_timeout(500)
    raise RuntimeError(f"在 {timeout}ms 內找不到含 canvas 的遊戲 iframe")


@pytest.mark.skip(reason="dev 遊戲 launch 已知問題：launchLoading 頁未渲染 iframe/canvas，疑似遊戲商戶未申請或遊戲下架。依團隊決定暫時 skip（rc/re/rd 一致），待 dev 遊戲後端修復後移除此 skip。")
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
        game_frame = _get_game_frame(new_page, timeout=30000)
        new_page.wait_for_timeout(3000)

        canvas_count = game_frame.evaluate("() => document.querySelectorAll('canvas').length")
        assert canvas_count > 0, f"遊戲 iframe 內找不到 canvas（count={canvas_count}）"
