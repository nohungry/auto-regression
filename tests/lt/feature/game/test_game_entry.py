"""
LT 前台遊戲進入與下注測試
LT-GAME-001

使用自動化會員帳號 dltauto02 登入前台，
導覽至電子分類 → 選擇 T9電子 → 點擊關老爺 →
遊戲在新分頁開啟 → 開始 → 確定機台 → 減注(8→4) → Spin →
遊戲內查注單 → 關閉遊戲回主站查投注紀錄。

與 RC 站差異：
- LT 只有一個 T9電子（直接點 provider tile）
- 遊戲卡片無文字標籤（用 img src 定位）
- 點擊遊戲後開啟新分頁（非 iframe）
- Canvas 高度 826 vs RC 762，Y 座標偏低 2-3%
- LT 用 hamburger drawer 查投注紀錄（非 sidebar-item）
"""

import re
import time
import pytest
from playwright.sync_api import Page, Frame, expect, TimeoutError as PlaywrightTimeoutError
from pages.lt.login_page import LoginPage
from pages.lt.home_page import HomePage
from utils.screenshot_helper import get_screenshotter


# 自動化會員帳號
MEMBER_USER = "dltauto02"
MEMBER_PASS = "Ab123456!"

# 遊戲路徑
CATEGORY_NAV = "電子"
PROVIDER_NAME = "T9電子"
GAME_NAME = "關老爺"

# LT canvas=826高，座標經 grid search/截圖實測驗證
GAME_BTN = {
    "開始":    (0.50, 0.92),
    "確定":    (0.78, 0.86),   # grid search 驗證
    "spin":   (0.90, 0.85),   # start_spin API 驗證
    "選單":    (0.93, 0.60),   # 截圖驗證（側邊欄成功展開）
    "紀錄":    (0.88, 0.47),   # 從展開側邊欄截圖量測
}

# 減注候選位置（grid search 有效但單點不穩，快速連點 3 位確保命中）
REDUCE_BET_CANDIDATES = [
    (0.59, 0.95), (0.61, 0.95), (0.59, 0.97),
]


@pytest.mark.p1
@pytest.mark.lt
@pytest.mark.game
class TestGameEntry:
    """LT-GAME-001：前台遊戲進入與下注流程"""

    def test_enter_and_spin(self, page: Page, site_config):
        """LT-GAME-001：登入 → 電子 → T9電子 → 關老爺(新分頁) → 開始 → 確定 → 減注 → Spin → 注單驗證"""
        sh = get_screenshotter(page)

        # ===== Phase 1: 前台導覽至遊戲 =====

        login = LoginPage(page, site_config.url)
        login.goto_and_login(MEMBER_USER, MEMBER_PASS)

        home = HomePage(page)
        home.verify_login_success(MEMBER_USER)
        page.wait_for_timeout(2000)

        # 電子分類
        home.click_nav_item(CATEGORY_NAV)
        page.wait_for_timeout(3000)

        # 選 T9電子（LT 用 provider tile 直接點擊）
        provider = page.locator("div.group", has_text=PROVIDER_NAME).first
        provider.wait_for(state="visible", timeout=5000)
        provider.click(force=True)
        page.wait_for_timeout(5000)

        # 點關老爺（用圖片 src 定位，LT 遊戲卡片無文字）
        game_img = page.locator('img[src*="GuanGong"], img[src*="SL2570"]').first
        game_img.wait_for(state="visible", timeout=10000)
        game_card = game_img.locator("xpath=ancestor::div[contains(@class,'cursor-pointer')][1]")

        # 用 expect_page 捕捉新分頁
        with page.context.expect_page(timeout=30000) as new_page_info:
            game_card.click(force=True)
        game_page = new_page_info.value

        # 等待遊戲 canvas 載入
        game_page.locator("canvas").first.wait_for(state="attached", timeout=30000)
        game_page.wait_for_timeout(10000)

        # ===== Phase 2: 遊戲內操作（CDP）=====

        cdp = game_page.context.new_cdp_session(game_page)

        try:
            canvas_box = game_page.locator("canvas").first.bounding_box()
            assert canvas_box, "找不到遊戲 canvas"

            def game_click(btn_name: str, wait_after: int = 2000):
                x_pct, y_pct = GAME_BTN[btn_name]
                abs_x = canvas_box["x"] + canvas_box["width"] * x_pct
                abs_y = canvas_box["y"] + canvas_box["height"] * y_pct

                cdp.send("Input.dispatchMouseEvent", {
                    "type": "mousePressed",
                    "x": abs_x, "y": abs_y,
                    "button": "left", "clickCount": 1
                })
                cdp.send("Input.dispatchMouseEvent", {
                    "type": "mouseReleased",
                    "x": abs_x, "y": abs_y,
                    "button": "left", "clickCount": 1
                })
                game_page.wait_for_timeout(wait_after)

            # 開始 → 機台選擇
            game_click("開始", wait_after=10000)

            # 確定機台 → 進入遊戲
            game_click("確定", wait_after=12000)

            # 減注（8→4）：LT 座標不穩定，快速嘗試多個候選位置
            for xp, yp in REDUCE_BET_CANDIDATES:
                abs_x = canvas_box["x"] + canvas_box["width"] * xp
                abs_y = canvas_box["y"] + canvas_box["height"] * yp
                cdp.send("Input.dispatchMouseEvent", {
                    "type": "mousePressed",
                    "x": abs_x, "y": abs_y,
                    "button": "left", "clickCount": 1
                })
                cdp.send("Input.dispatchMouseEvent", {
                    "type": "mouseReleased",
                    "x": abs_x, "y": abs_y,
                    "button": "left", "clickCount": 1
                })
                game_page.wait_for_timeout(300)

            # 監聽 start_spin API
            spin_api_called = []
            game_page.on("request", lambda req: (
                spin_api_called.append(req.url)
                if "start_spin" in req.url else None
            ))

            # Spin 下注
            game_click("spin", wait_after=10000)

            # ===== Phase 3: 遊戲內查注單紀錄 =====

            # 點漢堡選單展開側邊欄
            game_click("選單", wait_after=2000)

            # 點紀錄
            game_click("紀錄", wait_after=3000)

            # 截圖記錄遊戲內注單
            game_page.screenshot(path="screenshots/lt_game_注單紀錄.png")

        finally:
            cdp.detach()

        # 驗證 start_spin API 被呼叫
        assert len(spin_api_called) > 0, (
            "Spin API (start_spin) 未被呼叫，下注失敗"
        )

        # ===== Phase 4: 關閉遊戲，回主站查投注紀錄 =====

        game_page.close()
        page.bring_to_front()
        page.wait_for_timeout(2000)

        # 用 LT 的 hamburger drawer 查投注紀錄
        home.open_betting_history_dialog()

        # 等待投注紀錄 dialog 載入
        dialog = page.locator(".dialog-container")
        dialog.wait_for(state="visible", timeout=5000)
        page.wait_for_timeout(1000)

        if sh:
            sh.full_page("verify_投注紀錄_dialog打開")

        # 點擊「今日」快捷篩選
        today_btn = dialog.locator("text=今日").first
        today_btn.scroll_into_view_if_needed()
        today_btn.click(force=True)
        page.wait_for_timeout(1000)

        # 點擊「搜尋」按鈕
        search_btn = dialog.locator("text=搜尋").first
        search_btn.scroll_into_view_if_needed()
        search_btn.click(force=True)
        page.wait_for_timeout(3000)

        if sh:
            sh.full_page("verify_投注紀錄_注單結果")

        # 驗證注單紀錄存在
        no_data = dialog.locator("text=尚無任何資料")
        has_data = not no_data.is_visible()
        assert has_data, "投注紀錄應有注單，但顯示「尚無任何資料」"
