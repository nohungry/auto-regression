"""
首頁 Page Object — lu 站點（Dlgbet）
登入成功後的首頁驗證、彈窗清理、登出

probe 結果（selector-explorer 2026-06-05；與 LG 結構差異大）：
- LU 不顯示 username（nav/sidebar 皆無帳號名）→ 已登入信號用 nav 餘額 span +
  登入 CTA（button.neon-btn）消失，不可用 to_contain_text(username)
- 無 avatar dropdown：登出功能在左側 sidebar；點 hamburger button.nav-toggle-btn
  展開 sidebar（70px → 270px），登出是真 <button>（收合時 lg:hidden）
- 進站雙層彈窗：圖片廣告（button.popup-close-btn）+ 文字公告（.close-wrap）
- nav 遊戲分類以頁面 card 呈現：a[href*='/Categories/']（6 個）
- Tailwind arbitrary-value class 方括號在 selector 內需跳脫（Python 字串為 \\[ \\]）
"""

from playwright.sync_api import Page, expect, TimeoutError as PlaywrightTimeoutError
from utils.game_launch_helper import open_in_new_tab
from utils.menu_helper import leaf_menu_texts
from utils.screenshot_helper import get_screenshotter


class HomePage:

    # 電子(slots)分類：href pathname（LU nav 為 href-based）
    SLOTS_CATEGORY = "/Categories/slots"
    # 遊戲卡 launch 目標：LU 每張遊戲卡為 div.card-item（直接點卡片啟動，無 hover overlay）
    GAME_CARD = "div.card-item.mb-1"

    def __init__(self, page: Page):
        self.page = page

        # 已登入信號：nav 餘額數字 span（登入後才渲染）
        self.balance = page.locator(
            ".fixed.top-0.z-50 span.text-xs.font-bold.text-white"
        ).first
        # 未登入信號：nav 登錄 CTA（灰底 .bg-shade03，與登入後金色 icon neon-btn 區分）
        self.login_cta = page.locator(
            ".fixed.top-0.z-50 button.neon-btn.bg-shade03"
        ).first

        # 左側 sidebar 與 hamburger
        self.nav_toggle = page.locator("button.nav-toggle-btn").first
        # 2026-07-23 站點改版：sidebar 容器改為 #sidebar（z-30 → z-[99]，icon-rail 設計）
        self.sidebar = page.locator("#sidebar").first

        # 頂部 nav 存提入口（2026-07-24 probe：桌面皆可見；點擊開錢包 dialog、URL 不變；
        # LU 殘留 .dialog-mask 攔 pointer → 互動用 dispatch_event 站慣例）
        self.deposit_btn = page.locator(".fixed.top-0.z-50 button.neon-btn").first
        self.withdraw_btn = page.locator(".fixed.top-0.z-50 button", has_text="提現").first
        # 2026-08-10 改版：容器寬度 class 由 max-w-[612px] 改為
        # min-w-full lg:min-w-[600px] lg:max-w-[600px]；取 lg:max-w-[600px] 定位。
        self.wallet_dialog = page.locator(".dialog-container.lg\\:max-w-\\[600px\\]").first
        # 錢包 dialog 內部（2026-08-10 probe）：存款/提現分頁、付款平台格線、送出鈕。
        # 格線為 grid grid-cols-3，每格一個付款平台（無 id/data-*，以結構定位）。
        self.wallet_tabs = self.wallet_dialog.locator("div.cursor-pointer p.font-bold")
        self.payment_platform_grid = self.wallet_dialog.locator("div.grid.grid-cols-3").first
        self.payment_platforms = self.payment_platform_grid.locator("> div")
        self.wallet_submit_btn = self.wallet_dialog.locator("button.main-btn").first
        # user menu 容器別名（sidebar feature 用；LU 即左側 sidebar）
        self.user_menu = self.sidebar
        # 登出 button（sidebar 展開後唯一 button，class 含 border-shade04）
        # 2026-07-23 sidebar 改版：容器改 #sidebar；收合時 lg:hidden、hamburger 展開後可見
        # （Playwright 原生 click 展開正常；agent-browser dispatchEvent 探勘曾誤判 toggle 失效）
        self.logout_btn = page.locator(
            "#sidebar button[class*='border-shade04']"
        ).first

        # 進站雙層彈窗關閉鈕
        self.ad_popup_close = page.locator("button.popup-close-btn")
        # 用 max-w-[840px] 精準鎖定公告（錯誤 modal 也含 w-full + close-wrap，避免命中 2 個）
        self.announce_close = page.locator(
            ".dialog-container.max-w-\\[840px\\] .close-wrap"
        )

    # ------------------------------------------------------------------
    # 登入狀態驗證
    # ------------------------------------------------------------------

    def is_logged_in(self) -> bool:
        """判斷目前是否已登入（餘額 span 可見）"""
        try:
            return self.balance.is_visible(timeout=3000)
        except Exception:
            return False

    def verify_logged_in(self):
        """輕量驗證：nav 餘額 span 可見即代表已登入。"""
        sh = get_screenshotter(self.page)
        expect(self.balance).to_be_visible(timeout=10000)
        self.balance.scroll_into_view_if_needed()
        if sh: sh.capture(self.balance, "verify_已登入_餘額顯示")

    def verify_login_success(self, username: str):
        """驗證登入成功：nav 餘額 span 可見 + 登錄 CTA 消失。

        斷言策略：
        - 餘額 span 可見（登入後才渲染，明確已登入信號）
        - 登錄 CTA（button.neon-btn）不再可見（nav 由「登錄 註冊」變為「餘額 提現」）
        注意：LU 不顯示 username，故不對 username 字串斷言（與 LG/QW 不同）。
        username 參數僅作 screenshot label 用。
        """
        sh = get_screenshotter(self.page)

        expect(self.balance).to_be_visible(timeout=15000)
        self.balance.scroll_into_view_if_needed()
        if sh: sh.capture(self.balance, f"verify_餘額顯示_{username}")

        expect(self.login_cta).not_to_be_visible(timeout=5000)

    def verify_logged_out(self):
        """驗證已登出：首頁登錄 CTA 重新出現。"""
        sh = get_screenshotter(self.page)
        expect(self.login_cta).to_be_visible(timeout=10000)
        self.login_cta.scroll_into_view_if_needed()
        if sh: sh.capture(self.login_cta, "verify_已登出_登錄按鈕出現")

    # ------------------------------------------------------------------
    # 彈窗清理
    # ------------------------------------------------------------------

    def dismiss_any_popups(self):
        """依序關閉進站雙層彈窗（圖片廣告 → 文字公告）。"""
        try:
            self.ad_popup_close.wait_for(state="visible", timeout=1500)
            self.ad_popup_close.dispatch_event("click")
            self.ad_popup_close.wait_for(state="hidden", timeout=2000)
        except PlaywrightTimeoutError:
            pass
        try:
            self.announce_close.wait_for(state="visible", timeout=1500)
            self.announce_close.dispatch_event("click")
            self.page.locator(".dialog-container.max-w-\\[840px\\]").first.wait_for(
                state="hidden", timeout=2000
            )
        except PlaywrightTimeoutError:
            pass

    # ------------------------------------------------------------------
    # 導覽
    # ------------------------------------------------------------------

    def click_nav_item(self, category_path: str):
        """點擊指定遊戲分類連結（a[href='/Categories/<x>']）導航。

        LU nav 為 href-based（無 ul.nav-item）；用 dispatch_event 直觸 DOM click，
        繞過 fresh 載入 ~10s 才出現的進站公告 mask（避免 pointer 攔截）。
        category_path 傳完整 pathname，如 "/Categories/slots"。
        """
        sh = get_screenshotter(self.page)
        if sh: sh.full_page(f"before_click_{category_path.rsplit('/', 1)[-1]}")
        self.page.locator(f"a[href='{category_path}']").first.dispatch_event("click")

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

        LU 流程：點 div.card-item → window.open 新分頁 → /launchLoading →
        轉址至第三方 provider 遊戲（royalgaming777 EnterGame2 等）。
        index 用於跳過個別壞掉的遊戲（部分 provider 遊戲可能在 staging 啟動失敗）。

        新分頁處理（等分頁 + maximize）走 utils.game_launch_helper.open_in_new_tab。
        """
        return open_in_new_tab(
            self.page,
            self.page.locator(self.GAME_CARD).nth(index),
            label=f"click_啟動遊戲_第{index}款",
            screenshotter=get_screenshotter(self.page),
        )

    # ------------------------------------------------------------------
    # 會員中心 / 錢包
    # ------------------------------------------------------------------

    def open_user_menu(self):
        """展開左側 sidebar（hamburger），等登出 button 可見（sidebar 開啟信號）。"""
        self.dismiss_any_popups()
        self.nav_toggle.dispatch_event("click")
        expect(self.logout_btn).to_be_visible(timeout=5000)

    def user_menu_item_texts(self) -> list:
        """回傳已開啟 user menu（左 sidebar）內的項目文字（葉節點短文字、去重）。

        供 sidebar feature 驗證選單結構完整性（與 member 的導航驗證區隔）。
        LU 的 user_menu 是左側 sidebar（與 LG 的 avatar dropdown 結構不同），
        呼叫前須先 open_user_menu()。

        葉節點文字抽取走 utils.menu_helper.leaf_menu_texts。
        """
        return leaf_menu_texts(self.user_menu)

    def click_member_link(self, type_key: str):
        """開 sidebar 後點 member 連結（a[href*='type=<key>']）。

        LU sidebar 的可導航會員連結為 /member?type=X（MemberMessage 信件 / AllAgent
        全民代理）；我的帳戶/存款/提現為 in-panel JS handler（非 URL），本方法不涵蓋。
        """
        sh = get_screenshotter(self.page)
        self.open_user_menu()
        link = self.page.locator(f"a[href*='type={type_key}']").first
        if sh: sh.capture(link, f"click_member_{type_key}")
        link.dispatch_event("click")

    # ------------------------------------------------------------------
    # 登出
    # ------------------------------------------------------------------

    def open_deposit_dialog(self):
        """點頂部 nav 儲值 +（neon-btn）開錢包 dialog（in-page modal，URL 不變）。"""
        sh = get_screenshotter(self.page)
        if sh: sh.capture(self.deposit_btn, "click_儲值入口")
        self.deposit_btn.dispatch_event("click")
        self.wallet_dialog.wait_for(state="visible", timeout=8000)
        if sh: sh.full_page("verify_錢包dialog_儲值")

    def open_withdraw_dialog(self):
        """點頂部 nav 提現 button 開錢包 dialog（與儲值共用同一容器）。"""
        sh = get_screenshotter(self.page)
        if sh: sh.capture(self.withdraw_btn, "click_提現入口")
        self.withdraw_btn.dispatch_event("click")
        self.wallet_dialog.wait_for(state="visible", timeout=8000)
        if sh: sh.full_page("verify_錢包dialog_提現")

    def wallet_tab_texts(self) -> list:
        """回傳錢包 dialog 分頁文字（預期 ['存款', '提現']）。"""
        return [
            self.wallet_tabs.nth(i).inner_text().strip()
            for i in range(self.wallet_tabs.count())
        ]

    def payment_platform_texts(self) -> list:
        """回傳付款平台格線內各平台的顯示文字（含金額區間行，如 'GrabPay\\n1 - 50000'）。

        存款分頁專屬；提現分頁無此格線。呼叫端須先 open_deposit_dialog()。
        """
        self.payment_platform_grid.wait_for(state="visible", timeout=8000)
        return [
            self.payment_platforms.nth(i).inner_text().strip()
            for i in range(self.payment_platforms.count())
        ]

    def logout(self):
        """登出：點 hamburger 展開左側 sidebar → click 登出 button → 驗證登出。

        LU 登出在左側 sidebar（無 avatar dropdown）。sidebar 收合時登出 button
        為 lg:hidden，必須先展開。登出後登錄 CTA 重現。
        """
        sh = get_screenshotter(self.page)

        self.dismiss_any_popups()

        # 展開 sidebar
        if sh: sh.capture(self.nav_toggle, "click_展開sidebar")
        self.nav_toggle.dispatch_event("click")

        # 等登出 button 可見（sidebar 展開後才顯示）
        expect(self.logout_btn).to_be_visible(timeout=5000)
        # sidebar 展開後 logout_btn bbox 在視窗外 → 整頁截圖呈現展開狀態，紅框無意義
        if sh: sh.full_page("verify_sidebar_opened")

        # 點登出
        if sh: sh.full_page("click_登出")
        self.logout_btn.dispatch_event("click")

        # 驗證登出成功：登錄 CTA 重現
        expect(self.login_cta).to_be_visible(timeout=10000)
        self.login_cta.scroll_into_view_if_needed()
        if sh: sh.capture(self.login_cta, "verify_登出成功")
