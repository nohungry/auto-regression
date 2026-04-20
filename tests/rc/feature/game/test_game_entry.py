"""
RC 前台遊戲進入與下注測試
RC-GAME-001

使用 .env 的 SITE_RC_USERNAME 登入前台，
導覽至電子分類 → 選擇 T9電子 → 點擊關老爺 →
點「開始」→ 機台確認 → 調整押注至 4 元 → Spin 下注。

遊戲渲染在 iframe 內的 canvas，所有遊戲內操作使用
單一持久 CDP session 的 Input.dispatchMouseEvent。
重要：必須在整個遊戲階段共用同一個 CDP session，
每次建新 session 會干擾遊戲引擎的事件處理。
"""

import re
import time
import pytest
from playwright.sync_api import Page, Frame, expect, TimeoutError as PlaywrightTimeoutError
from pages.rc.login_page import LoginPage
from pages.rc.home_page import HomePage
from utils.dialog_helper import wait_loading_if_present
from utils.screenshot_helper import get_screenshotter


# 會員帳號從 .env 的 SITE_RC_USERNAME / SITE_RC_PASSWORD 讀取（透過 site_config）

# 遊戲路徑
CATEGORY_NAV = "電子"
PROVIDER_NAME = "T9電子"
GAME_NAME = "關老爺"

# 遊戲內按鈕位置（百分比座標，相對於 iframe bounding box）
GAME_BTN = {
    "開始":    (0.50, 0.92),
    "確定":    (0.78, 0.88),   # 機台選擇確認（modal 右下角）
    "減注":    (0.62, 0.94),   # 「-」按鈕
    "spin":   (0.90, 0.85),   # Spin 大綠按鈕（實測 start_spin API 觸發位置）
    "選單":    (0.90, 0.60),   # 三條橫線（漢堡選單），機台圖標(0.53)下方
    "紀錄":    (0.88, 0.46),   # 側邊欄展開後「紀錄」按鈕（設定在0.55，往上調）
}


def _get_game_frame(page: Page, timeout: int = 30000) -> Frame:
    """等待包含 canvas 的遊戲 iframe 出現"""
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


@pytest.mark.p1
@pytest.mark.rc
@pytest.mark.game
@pytest.mark.skip(
    reason="Phase 2 iframe 內 start_spin 座標/遊戲行為在 dev-rc 尚未穩定；"
           "Phase 1 (電子→T9電子→關老爺) dropdown 攔截已用 dispatch_event 修好。"
           "見 memory: project_dev_rc_latency_2026_04.md"
)
class TestGameEntry:
    """RC-GAME-001：前台遊戲進入與下注流程"""

    def test_enter_and_spin(self, page: Page, site_config):
        """RC-GAME-001：登入 → 電子 → T9電子 → 關老爺 → 開始 → 確定 → 減注 → Spin"""
        sh = get_screenshotter(page)

        # ===== Phase 1: 前台導覽至遊戲 =====

        login = LoginPage(page, site_config.url)
        login.goto_and_login(site_config.username, site_config.password)
        home = HomePage(page)
        home.verify_login_success(site_config.username)
        home.dismiss_any_popups()

        home.click_nav_item(CATEGORY_NAV)
        expect(page).to_have_url(re.compile("Categories/slots"), timeout=8000)

        # .game-type 展開後 dropdown (data-id="1") 會覆蓋下方內容並攔截 pointer events，
        # platform / game card 點擊都受影響。整段改用 dispatch_event 直接觸發。
        page.locator(".game-type").first.dispatch_event("click")
        platform_btn = page.locator(".platform-list-bg").locator(f"text={PROVIDER_NAME}").first
        platform_btn.wait_for(state="visible", timeout=8000)
        platform_btn.dispatch_event("click")
        wait_loading_if_present(page)

        game_card = page.locator(f"text={GAME_NAME}").first
        game_card.wait_for(state="visible", timeout=8000)
        game_card.dispatch_event("click")

        # 等待遊戲 iframe + canvas
        _get_game_frame(page, timeout=30000)
        page.wait_for_timeout(3000)  # 等遊戲引擎初始化
        if sh:
            sh.full_page("verify_遊戲載入完成")

        # ===== Phase 2: 遊戲內操作 =====
        # 建立單一持久 CDP session（整個遊戲階段共用）
        cdp = page.context.new_cdp_session(page)

        try:
            iframe_box = page.locator("iframe").first.bounding_box()
            assert iframe_box, "找不到遊戲 iframe"

            def game_click(btn_name: str, wait_after: int = 2000):
                """使用共用 CDP session 點擊遊戲按鈕"""
                x_pct, y_pct = GAME_BTN[btn_name]
                abs_x = iframe_box["x"] + iframe_box["width"] * x_pct
                abs_y = iframe_box["y"] + iframe_box["height"] * y_pct

                if sh:
                    sh.full_page(f"click_遊戲_{btn_name}_before")

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

                page.wait_for_timeout(wait_after)

                if sh:
                    sh.full_page(f"click_遊戲_{btn_name}_after")

            # 開始 → 機台選擇
            game_click("開始", wait_after=8000)

            # 確定機台 → 進入遊戲
            game_click("確定", wait_after=10000)

            # 減注（8→4）
            game_click("減注", wait_after=1000)

            # Spin 下注：用 expect_request 保證 listener 在 click 前啟動，
            # 並把 start_spin API 呼叫作為硬性 assertion（未觸發會 timeout）
            if sh:
                sh.full_page("verify_下注前")
            with page.expect_request("**/start_spin**", timeout=15000) as spin_req:
                game_click("spin", wait_after=6000)
            spin_request_url = spin_req.value.url

            if sh:
                sh.full_page("verify_Spin結果")

            # ===== Phase 3: 遊戲內查注單紀錄 =====

            # 點漢堡選單展開側邊欄
            game_click("選單", wait_after=2000)

            # 點紀錄
            game_click("紀錄", wait_after=3000)

            if sh:
                sh.full_page("verify_遊戲內注單紀錄")

        finally:
            cdp.detach()

        # expect_request 已於 spin click 時硬性保證 start_spin 被觸發，
        # 這裡做一個 trace 用的輸出即可
        assert spin_request_url, "start_spin API URL 為空"

        # ===== Phase 4: 回到主站查遊戲明細 =====

        # 點「回到大廳」→ 會出現「退出遊戲」確認彈窗
        back_btn = page.locator("text=回到大廳").first
        back_btn.click()
        page.wait_for_timeout(2000)

        # 處理「退出遊戲」確認：點擊確定（橘色按鈕）
        exit_confirm = page.locator("text=確定").first
        try:
            exit_confirm.wait_for(state="visible", timeout=5000)
            exit_confirm.click()
        except PlaywrightTimeoutError:
            pass

        page.wait_for_load_state("networkidle")
        wait_loading_if_present(page)
        page.wait_for_timeout(3000)
        home.dismiss_any_popups()

        # 開啟「遊戲明細」側邊欄（RC sidebar hidden node，用 dispatch_event）
        game_details = page.locator(".sidebar-item.game-details")
        game_details.dispatch_event("click")

        # 等待遊戲明細 dialog 出現
        dialog = page.locator(".dialog-container")
        dialog.wait_for(state="visible", timeout=5000)
        page.wait_for_timeout(1000)

        if sh:
            sh.full_page("verify_遊戲明細_dialog打開")

        # 點擊「今日」快捷篩選（在 dialog 內部）
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
            sh.full_page("verify_遊戲明細_注單紀錄")

        # 驗證注單紀錄存在
        no_data = dialog.locator("text=尚無任何資料")
        has_data = not no_data.is_visible()
        assert has_data, "遊戲明細應有注單紀錄，但顯示「尚無任何資料」"
