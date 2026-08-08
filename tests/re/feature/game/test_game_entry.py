"""
RE 前台遊戲進入與下注測試 (BeWin)
RE-GAME-001

使用 .env 的 SITE_RE_USERNAME 登入前台，
導覽至電子分類 → 選擇 T9電子 → 點擊關老爺 →
點「開始」→ 機台確認 → 調整押注至 4 元 → Spin 下注。

遊戲渲染在 iframe 內的 canvas，所有遊戲內操作使用
單一持久 CDP session 的 Input.dispatchMouseEvent。
重要：必須在整個遊戲階段共用同一個 CDP session，
每次建新 session 會干擾遊戲引擎的事件處理。

為何不用 Playwright page.mouse.click？
2026-05-09 實機驗證：在 RE iframe canvas 上 page.mouse.click(abs_x, abs_y)
完全不觸發「確定」按鈕的 click handler（machine select dialog 不會關），
spin click 也打不到 — start_spin API timeout。CDP raw mouse event 才能
驅動 RE 的 canvas event 系統。屬 RE 平台特性，非 over-engineering。

與 tests/rc/feature/game/test_game_entry.py 雖然都跑同平台同款遊戲，
但 GAME_BTN 座標已 fork（RE iframe 1920x1015 與 RC 1536x762 比例不同；
RE 機台 select dialog 流程也與 RC 微異）— 修改座標時請各自獨立調整，
不要互相 sync。
"""

import re
import pytest
from playwright.sync_api import Page, expect, TimeoutError as PlaywrightTimeoutError
from pages.factory import get_login_page_class, get_home_page_class
from utils.dialog_helper import wait_loading_if_present
from utils.game_launch_helper import get_game_frame
from utils.screenshot_helper import get_screenshotter


LoginPage = get_login_page_class("re")
HomePage = get_home_page_class("re")


# 會員帳號從 .env 的 SITE_RE_USERNAME / SITE_RE_PASSWORD 讀取（透過 site_config）

# 遊戲路徑
CATEGORY_NAV = "電子"
PROVIDER_NAME = "T9電子"
GAME_NAME = "關老爺"

# 遊戲內按鈕位置（百分比座標，相對於 iframe bounding box）
# RE 與 RC 的關鍵差異：
# - RE iframe 1920x1015（RC 是 1536x762），canvas UI 元素為固定像素位置 → 百分比不同
# - RE 機台選擇 dialog 比 RC 多一個 「點機台 → 選取 → 確認 popup」的步驟（RC 直接 確定 進遊戲）
# - 座標經 PIL 找橘色 button center 校準（pages/dashboard/re/management_page.py 同樣手法）
GAME_BTN = {
    "開始":   (0.50, 0.92),  # 預覽畫面綠色開始 button
    "確定":   (0.78, 0.85),  # 機台 select dialog 右下橘色「確定」(PIL 校準；默認機台直接 confirm)
    "減注":   (0.62, 0.94),  # 「-」按鈕
    "spin":  (0.90, 0.85),  # Spin 大綠按鈕（實測 start_spin API 觸發位置）
    "選單":   (0.90, 0.60),  # 三條橫線（漢堡選單）
    "紀錄":   (0.88, 0.46),  # 側邊欄展開後「紀錄」按鈕
}


@pytest.mark.p1
@pytest.mark.re
@pytest.mark.game
class TestGameEntry:
    """RE-GAME-001：前台遊戲進入與下注流程"""

    def test_enter_and_spin(self, page: Page, site_config):
        """RE-GAME-001：登入 → 電子 → T9電子 → 關老爺 → 開始 → 確定 → 減注 → Spin"""
        sh = get_screenshotter(page)

        # ===== Phase 1: 前台導覽至遊戲 =====

        login = LoginPage(page, site_config.url)
        login.goto_and_login(site_config.username, site_config.password)
        home = HomePage(page)
        home.verify_login_success(site_config.username)
        home.dismiss_any_popups()

        home.click_nav_item(CATEGORY_NAV)
        expect(page).to_have_url(re.compile("Categories/slots"), timeout=8000)

        # .game-type 展開後 dropdown 會覆蓋下方內容並攔截 pointer events，
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
        get_game_frame(page, timeout=30000)
        # RE 的 game asset 載入較慢（實機觀察 loading bar 從 0 → 100% 約需 12-15s）；
        # RC 用 3s 即可進入 preview，RE 必須等 15s 否則點 開始 會打在 99% loading 畫面被吞掉
        page.wait_for_timeout(15000)
        if sh:
            sh.full_page("verify_遊戲載入完成")

        # ===== Phase 2: 遊戲內操作 =====
        # 為何用 CDP Input.dispatchMouseEvent 而非 Playwright page.mouse.click？
        # 實驗 2026-05-09：把 game_click 換成 page.mouse.click(abs_x, abs_y) 跑同一
        # 流程，「確定」button 完全不被觸發（machine select dialog 沒關，spin
        # click 落在 dialog 上 → start_spin API timeout）。CDP raw mouse event
        # 才能觸發 RE 遊戲 iframe canvas 的 click handler — 與 RC iframe 行為差異。
        # 結論：CDP 是 RE 必要的 workaround，不是 over-engineering。
        # （此差異也是當初 Luke 把 RC test 與 RE test 都用 CDP 統一的原因。）
        cdp = page.context.new_cdp_session(page)

        try:
            iframe_box = page.locator("iframe").first.bounding_box()
            assert iframe_box, "找不到遊戲 iframe"

            def game_click(btn_name: str, wait_after: int = 2000):
                """使用共用 CDP session 點擊遊戲按鈕（Playwright click 在 RE 不 work）"""
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

            # 開始 → 機台選擇 dialog
            game_click("開始", wait_after=8000)

            # 確定 → 用 default 機台直接進遊戲（同 RC 流程，只是座標不同）
            # 註：若點到機台才按確定 → 變成「選取」會跳 popup「將切換到 X 號桌」
            #     避免那條 path，直接點 確定 即可；座標來自 PIL 校準（橘色 button center）
            game_click("確定", wait_after=12000)

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

        # 開啟「遊戲明細」側邊欄
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
