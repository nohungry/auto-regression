"""
首頁 Page Object — lg 站點（大撈家娛樂城）
登入成功後的首頁驗證、彈窗清理、登出

probe 結果（selector-explorer 2026-06-05）：
- LG avatar 圖 alt="" → 不能用 QW 的 img[alt="avatar"]
- 已登入信號改用 .nav-bg .balance-color（餘額文字，登入後才渲染）
- username 顯示在 nav；用 .nav-bg 整體 to_contain_text(username) 驗證（robust，不綁特定 p）
- avatar dropdown 由 CLICK toggle（非 QW 的 hover）：點 avatar 圓圈容器 →
  右側滑入 .w-[280px] panel（translate-x-0 開 / translate-x-full 關）
- 登出按鈕是 div（非 button）：div.h-10.cursor-pointer.rounded-[10px].border，用 dispatch_event 觸發
- 本帳號登入後無 TOTP/安全中心彈窗；dismiss_any_popups 只處理進站公告
- Tailwind arbitrary-value class 方括號在 selector 內需跳脫（Python 字串為 \\[ \\]）
"""

import re
from playwright.sync_api import Page, expect, TimeoutError as PlaywrightTimeoutError
from utils.screenshot_helper import get_screenshotter
from utils.window_helper import maximize_page


class HomePage:

    # 電子(slots)分類：nav 中文標籤
    SLOTS_CATEGORY = "電子"
    # 遊戲卡 launch 目標：LG 每張卡 hover overlay 內「開始遊戲」鈕（平時 display:none，
    # 共 46 個 == 該分類遊戲數；dispatch_event 直觸 Vue handler，不受 hidden / sticky banner 影響）
    GAME_CARD = "text=開始遊戲"

    def __init__(self, page: Page):
        self.page = page

        # 已登入信號：餘額文字（登入後才渲染，locale-agnostic CSS class）
        self.balance = page.locator(".nav-bg .balance-color")
        # nav 容器（用於 to_contain_text(username) 驗證帳號顯示）
        self.nav_bar = page.locator(".nav-bg")

        # 未登入信號：nav 登入 CTA（border-white 無背景）
        self.login_cta = page.locator("button.h-\\[30px\\].w-\\[90px\\]")

        # avatar 圓圈容器（click 觸發 dropdown）
        self.avatar_trigger = page.locator(
            ".nav-bg div.rounded-full.cursor-pointer"
        ).first
        # dropdown 內滑入 panel（translate-x-0 開 / translate-x-full 關）
        self.dropdown_panel = page.locator(".w-\\[280px\\].absolute").first
        # 登出按鈕（div，非 button）
        self.logout_btn = page.locator(
            "div.h-10.cursor-pointer.rounded-\\[10px\\].border"
        )

        # 進站公告彈窗關閉 X
        self.announce_close = page.locator(".dialog-container.w-full .close-wrap")

    # ------------------------------------------------------------------
    # 登入狀態驗證
    # ------------------------------------------------------------------

    def is_logged_in(self) -> bool:
        """判斷目前是否已登入（餘額元素可見）"""
        try:
            return self.balance.is_visible(timeout=3000)
        except Exception:
            return False

    def verify_logged_in(self):
        """輕量驗證：餘額元素可見即代表已登入。無副作用。"""
        sh = get_screenshotter(self.page)
        expect(self.balance).to_be_visible(timeout=10000)
        self.balance.scroll_into_view_if_needed()
        if sh: sh.capture(self.balance, "verify_已登入_餘額顯示")

    def verify_login_success(self, username: str):
        """驗證登入成功：餘額元素可見 + nav 區塊文字含登入帳號。

        斷言策略：
        - .balance-color 可見（登入後才渲染，明確的已登入信號）
        - .nav-bg 整體文字含 username（robust，不對特定 p 斷言，避免 strict mode
          violation 與 fragile 的顏色 class）
        """
        sh = get_screenshotter(self.page)

        expect(self.balance).to_be_visible(timeout=15000)
        self.balance.scroll_into_view_if_needed()
        if sh: sh.capture(self.balance, "verify_餘額顯示")

        if sh: sh.capture(self.nav_bar, f"verify_帳號顯示_{username}")
        expect(self.nav_bar).to_contain_text(username, timeout=5000)

    def verify_logged_out(self):
        """驗證已登出：首頁登入 CTA 重新出現。"""
        sh = get_screenshotter(self.page)
        expect(self.login_cta).to_be_visible(timeout=10000)
        self.login_cta.scroll_into_view_if_needed()
        if sh: sh.capture(self.login_cta, "verify_已登出_登入按鈕出現")

    # ------------------------------------------------------------------
    # 彈窗清理
    # ------------------------------------------------------------------

    def dismiss_any_popups(self):
        """清除**登入後**首頁進站公告（probe 2026-06-06：公告為登入態 popup）。

        公告 = `.dialog-mask` + `.dialog-container.max-w-[840px]`，opacity:1、
        pointer-events:auto（會擋點擊）；close-wrap dispatch_event 後整個 mask 從 DOM
        移除（count→0）。注意：
        - close-wrap 剛出現時 boundingRect 為 0、非 "visible" → 用 `state="attached"` 等待。
        - dev 過載下公告延遲出現 → 等待放寬至 4s。
        - 未登入首頁不出現此公告（attached 等不到即 break，視為無公告）。
        """
        for _ in range(3):
            try:
                self.announce_close.wait_for(state="attached", timeout=4000)
            except PlaywrightTimeoutError:
                break  # 無公告（未登入 / 已關閉）
            self.announce_close.dispatch_event("click")
            try:
                # close 後整個 .dialog-mask 從 DOM 移除；等 count→0 確認不再攔截點擊
                self.page.wait_for_function(
                    "() => document.querySelectorAll('.dialog-mask').length === 0",
                    timeout=4000,
                )
                break
            except PlaywrightTimeoutError:
                continue

    # ------------------------------------------------------------------
    # 導覽
    # ------------------------------------------------------------------

    def click_nav_item(self, category_text: str):
        """點擊頂部 nav 主分類（ul.nav-item li，用文字過濾；每分類 count=1 無 hidden 節點）。

        前置：呼叫前須已 dismiss 進站公告（go_home 會做），否則殘留 mask 擋點擊。
        """
        sh = get_screenshotter(self.page)
        item = self.page.locator("ul.nav-item li").filter(has_text=category_text)
        item.scroll_into_view_if_needed()
        if sh: sh.capture(item, f"click_nav_{category_text}")
        item.click()

    # ------------------------------------------------------------------
    # 遊戲啟動
    # ------------------------------------------------------------------

    def open_slots_category(self):
        """導航至電子(slots)分類並等遊戲卡 grid 渲染（dev 慢，attached 等到 20s）。"""
        self.dismiss_any_popups()
        self.click_nav_item(self.SLOTS_CATEGORY)
        self.page.locator(self.GAME_CARD).first.wait_for(
            state="attached", timeout=20000
        )

    def game_card_count(self) -> int:
        """目前分類頁遊戲卡數量（grid 渲染健康度用）。"""
        return self.page.locator(self.GAME_CARD).count()

    def launch_game(self, index: int = 0) -> Page:
        """點第 index 張遊戲卡啟動遊戲，回傳另開的遊戲新分頁（已最大化）。

        LG 流程：點「開始遊戲」→ window.open 新分頁 → /launchLoading →
        轉址至第三方 provider launcher（gamelauncher，Slotmill 等）。
        新分頁不繼承最大化視窗，故 maximize_page() 校正座標/截圖（[[feedback-new-tab-maximize]]）。
        index 用於跳過個別壞掉的遊戲（部分 provider 遊戲可能在 staging 啟動失敗）。
        """
        sh = get_screenshotter(self.page)
        launcher = self.page.locator(self.GAME_CARD).nth(index)
        launcher.wait_for(state="attached", timeout=20000)
        if sh: sh.full_page(f"click_啟動遊戲_第{index}款")
        with self.page.context.expect_page(timeout=20000) as new_page_info:
            launcher.dispatch_event("click")
        game_page = new_page_info.value
        maximize_page(game_page)
        return game_page

    # ------------------------------------------------------------------
    # 會員中心 / 錢包
    # ------------------------------------------------------------------

    def open_user_menu(self):
        """開啟 avatar dropdown（右側滑入 panel），等 panel translate-x-0。"""
        self.dismiss_any_popups()
        self.avatar_trigger.dispatch_event("click")
        expect(self.dropdown_panel).to_have_class(
            re.compile(r"translate-x-0"), timeout=5000
        )

    def click_member_link(self, type_key: str):
        """開 user menu 後點 member-center 連結（a[href*='type=<key>']）。

        LG dropdown 連結為 /member-center?type=X（MyAccount/Deposit/Withdrawal/
        AccountDetails/MemberInbox 等）。用 dispatch_event 繞過動畫/overlay。
        """
        sh = get_screenshotter(self.page)
        self.open_user_menu()
        link = self.page.locator(f"a[href*='type={type_key}']").first
        if sh: sh.capture(link, f"click_member_{type_key}")
        link.dispatch_event("click")

    # ------------------------------------------------------------------
    # 登出
    # ------------------------------------------------------------------

    def logout(self):
        """登出：click avatar 圓圈 → 右側 dropdown 滑入 → click 登出 div → 驗證登出。

        LG dropdown 由 click toggle（非 QW 的 hover）。登出按鈕是 div，
        用 dispatch_event("click") 直觸 DOM event（避開滑入動畫與 overlay 攔截）。
        """
        sh = get_screenshotter(self.page)

        # 登出前再清一次公告，避免 mask 擋 avatar
        self.dismiss_any_popups()

        # 展開 dropdown
        if sh: sh.capture(self.avatar_trigger, "click_avatar開dropdown")
        self.avatar_trigger.dispatch_event("click")

        # 等右側 panel 滑入（class 出現 translate-x-0）
        expect(self.dropdown_panel).to_have_class(
            re.compile(r"translate-x-0"), timeout=5000
        )
        if sh: sh.capture(self.dropdown_panel, "verify_dropdown_opened")

        # 點登出（div，用 dispatch_event）
        if sh: sh.capture(self.logout_btn, "click_登出")
        self.logout_btn.dispatch_event("click")

        # 驗證登出成功：登入 CTA 重現
        expect(self.login_cta).to_be_visible(timeout=10000)
        self.login_cta.scroll_into_view_if_needed()
        if sh: sh.capture(self.login_cta, "verify_登出成功")
