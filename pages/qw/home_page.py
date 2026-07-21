"""
首頁 Page Object — qw 站點（LM來財娛樂城）
登入成功後的首頁驗證、彈窗清理、登出

probe 結果（2026-05-22；2026-06-25 補 sidebar/member）：
- Avatar：img[alt="avatar"]（與 RC 同 alt，巧合）
- Avatar 容器：.avatar-trigger（cursor-pointer）
- Username 顯示：.avatar-trigger p
- Dropdown：hover 觸發（非 click！Vue/Nuxt behavior）
  展開後 .avatar-menu__panel 顯示，內含 .avatar-menu__item（DIV，click 可 navigate）
  menu items（繁體）：帳戶管理/VIP特權/紅利禮包/銀行卡管理/帳戶明細/投注紀錄/
                      實時返水/全民代理/消息中心/個人信息 + button.avatar-menu__logout
  點 帳戶管理 → /member-center?type=MyAccount
- 登出按鈕：button.avatar-menu__logout
- 公告彈窗：.popup-mask（全屏 mask）+ .popup-close（X 按鈕）
- TOTP 提示：button，text 含「下次再說」（多語系：用 has_text 配合 try-except）

多語系注意：QW 多語系站（LaiBetLanguage cookie），不綁文案 selector。
登出按鈕用 CSS class（.avatar-menu__logout）而非文案。

注意：QW 無 KS 式右側 drawer；sidebar = avatar-menu__panel（hover dropdown）。
"""

from playwright.sync_api import Page, expect, TimeoutError as PlaywrightTimeoutError
from utils.screenshot_helper import get_screenshotter


class HomePage:

    def __init__(self, page: Page):
        self.page = page

        # 登入後主要元素
        self.avatar = page.locator('img[alt="avatar"]')
        self.avatar_trigger = page.locator('.avatar-trigger')

        # 未登入狀態：登入入口按鈕（多語系：用 CSS class）
        # probe 確認 class 為 .outline-btn-shared 或 .active-btn-shadow
        # 以 .outline-btn-shared 為主（較明確區分 login CTA）
        self.login_entry_btn = page.locator('button.outline-btn-shared').first

    # ------------------------------------------------------------------
    # 登入狀態驗證
    # ------------------------------------------------------------------

    def is_logged_in(self) -> bool:
        """判斷目前是否已登入（avatar 可見）"""
        try:
            return self.avatar.is_visible(timeout=3000)
        except Exception:
            return False

    def verify_logged_in(self):
        """輕量驗證：avatar 可見即代表已登入。無副作用。
        fixture 與單純確認登入狀態時使用。
        """
        sh = get_screenshotter(self.page)
        expect(self.avatar).to_be_visible(timeout=10000)
        self.avatar.scroll_into_view_if_needed()
        if sh: sh.capture(self.avatar, "verify_已登入_頭像")

    def verify_login_success(self, username: str):
        """驗證登入成功：avatar 可見 + .avatar-trigger 區塊含 username 文字。
        E2E 登入 TC 使用（test_login_success）。

        斷言策略：avatar visible + avatar_trigger 整體文字含 username。
        不對特定 p 元素斷言（avatar_trigger 內有 3 個 p：username、VIP 等級、餘額，
        會 strict mode violation；且各 p 的顏色 class fragile）。
        """
        sh = get_screenshotter(self.page)

        expect(self.avatar).to_be_visible(timeout=10000)
        self.avatar.scroll_into_view_if_needed()
        if sh: sh.capture(self.avatar, "verify_avatar_visible")

        self.avatar_trigger.scroll_into_view_if_needed()
        if sh: sh.capture(self.avatar_trigger, f"verify_帳號顯示_{username}")
        expect(self.avatar_trigger).to_contain_text(username, timeout=5000)

    def verify_logged_out(self):
        """驗證已登出：首頁登入入口按鈕重新出現。"""
        sh = get_screenshotter(self.page)
        expect(self.login_entry_btn).to_be_visible(timeout=10000)
        self.login_entry_btn.scroll_into_view_if_needed()
        if sh: sh.capture(self.login_entry_btn, "verify_已登出_登入按鈕出現")

    # ------------------------------------------------------------------
    # 彈窗清理
    # ------------------------------------------------------------------

    def dismiss_any_popups(self):
        """清除首頁可能出現的彈窗（公告 + TOTP 提示）。

        QW 兩種獨立 popup 系統（probe 2026-05-29）：
          1. 公告彈窗（首頁）— `.popup-mask` 容器 + `.popup-close` X 按鈕
          2. TOTP 安全中心提示（登入後）— `.dialog-mask` 容器 +
             `button.inactive-block.active-btn-shadow`（locale-agnostic，原文案「下次再說」）

        策略：loop 最多 3 輪 dismiss，直到兩種 mask 都完全消失或 timeout。
        TOTP 可能在公告 popup 關掉後才 render，所以單次 dismiss 不夠。
        """
        for _ in range(3):
            # 1. 公告彈窗
            try:
                popup_close = self.page.locator('.popup-close').first
                popup_close.wait_for(state="visible", timeout=1500)
                popup_close.click()
            except PlaywrightTimeoutError:
                pass

            # 2. TOTP 提示：用 CSS class 而非文案，跨 locale 不受影響
            # 「下次再說」按鈕的兩個關鍵 class（`inactive-block` + `active-btn-shadow`）
            # 在 TOTP dialog 內為唯一組合（probe verified）
            try:
                totp_dismiss = self.page.locator('button.inactive-block.active-btn-shadow').first
                totp_dismiss.wait_for(state="visible", timeout=1500)
                totp_dismiss.click()
            except PlaywrightTimeoutError:
                pass

            # 檢查兩個獨立 mask 系統都消失才退出 loop
            popup_hidden = True
            dialog_hidden = True
            try:
                self.page.locator('.popup-mask').first.wait_for(state="hidden", timeout=1000)
            except PlaywrightTimeoutError:
                popup_hidden = False
            try:
                self.page.locator('.dialog-mask').first.wait_for(state="hidden", timeout=1000)
            except PlaywrightTimeoutError:
                dialog_hidden = False
            if popup_hidden and dialog_hidden:
                break

    # ------------------------------------------------------------------
    # 導覽
    # ------------------------------------------------------------------

    def click_nav_category(self, data_id: int):
        """點擊頂部 nav 分類（ul.nav-item li[data-id='<N>'] span）。

        QW nav 分類為 span 而非 <a>，點擊後 URL 不變，僅切換 active class
        （li class 從 text-white 變成 text-[#FFC227]）。
        使用 data-id 屬性定位，避免綁死文案（probe 2026-06-24）：
          data-id=1 電子、2 真人、3 捕魚、4 棋牌、5 體育、6 彩票、7 鬥雞

        注意（probe 確認）：
        - dispatch_event("click") 不觸發 Vue click handler，active class 不切換。
          必須使用真實 Playwright .click()。
        - popup-mask 攔截 pointer events → 點前先 dismiss_any_popups()。
        """
        sh = get_screenshotter(self.page)
        self.dismiss_any_popups()
        li = self.page.locator(f"ul.nav-item li[data-id='{data_id}']").first
        if sh: sh.full_page(f"before_click_nav_{data_id}")
        li.click()

    def click_promotions_link(self):
        """點擊「優惠」連結（<a href='/promotions'>）並等待 URL 跳轉。

        優惠是 QW nav 中少數有真實 <a href> 的連結（其他分類為 span）。
        dispatch_event 繞過可能存在的 popup-mask overlay。
        不需先 dismiss popup（dispatch_event 直接觸發 DOM，不受 pointer events 影響）。
        """
        sh = get_screenshotter(self.page)
        self.dismiss_any_popups()
        link = self.page.locator("ul.nav-item li a[href='/promotions']").first
        if sh: sh.full_page("before_click_promotions")
        link.dispatch_event("click")

    def get_active_nav_category_text(self) -> str:
        """回傳目前 active 分類（li[data-id]）的文字。

        用於驗證 nav 點擊後 active 狀態切換。
        QW active li class：「text-[#FFC227] text-center hover:text-[#FFC227] ...」
        非 active li class：「text-white text-center hover:text-[#FFC227] ...」
        關鍵差異：active li 有無前綴的 text-[#FFC227]（非 hover:text-[...]）。
        透過 CSS class split 精準比對，避免與 hover: 前綴混淆。
        只看 li[data-id]（有 data-id = 分類 span，排除「首頁」<a>）。
        """
        result = self.page.evaluate(r"""() => {
            const items = document.querySelectorAll('ul.nav-item li[data-id]');
            for (const li of items) {
                // active li has 'text-[#FFC227]' WITHOUT 'hover:' prefix
                const classes = li.className.split(/\s+/);
                if (classes.includes('text-[#FFC227]')) {
                    return li.textContent.trim();
                }
            }
            return '';
        }""")
        return result or ""

    # ------------------------------------------------------------------
    # 登出
    # ------------------------------------------------------------------

    def logout(self):
        """登出：hover avatar_trigger 展開 dropdown → click 登出按鈕 → 驗證登出。

        QW avatar dropdown 由 hover 觸發（非 click，Vue/Nuxt behavior）。
        probe 確認 click 不展開，必須用 hover。
        """
        sh = get_screenshotter(self.page)

        # logout 之前再清一次彈窗（dismiss_any_popups loop 結束後 TOTP 提示可能才淡入完成）
        self.dismiss_any_popups()

        # 展開 dropdown：用 JS evaluate 派發 mouseenter/mouseover
        # 不用 Playwright hover()（即使 force=True，Vue 的 @mouseleave 仍可能立即觸發收起 dropdown；
        # JS dispatch 不會觸發後續 mouseleave，dropdown 維持 open 狀態）
        if sh: sh.capture(self.avatar_trigger, "hover_avatar_trigger")
        self.avatar_trigger.evaluate("""el => {
            const rect = el.getBoundingClientRect();
            const opts = { bubbles: true, cancelable: true,
                clientX: rect.left + rect.width / 2, clientY: rect.top + rect.height / 2 };
            el.dispatchEvent(new MouseEvent('mouseenter', opts));
            el.dispatchEvent(new MouseEvent('mouseover', opts));
        }""")

        # 等待 dropdown panel 出現
        avatar_menu_panel = self.page.locator('.avatar-menu__panel')
        expect(avatar_menu_panel).to_be_visible(timeout=5000)
        if sh: sh.capture(avatar_menu_panel, "verify_dropdown_opened")

        # 點擊登出按鈕（用 CSS class，locale-agnostic）
        # 注意：dropdown 由 hover 維持顯示；scroll_into_view 或一般 click 會打斷 hover
        # 導致 dropdown 收起 → element detach。改用 dispatch_event 直接派發 click DOM event。
        logout_btn = self.page.locator('button.avatar-menu__logout')
        if sh: sh.capture(logout_btn, "click_登出")
        logout_btn.dispatch_event("click")

        # 驗證登出成功：登入入口按鈕重新出現
        expect(self.login_entry_btn).to_be_visible(timeout=10000)
        self.login_entry_btn.scroll_into_view_if_needed()
        if sh: sh.capture(self.login_entry_btn, "verify_登出成功")

    # ------------------------------------------------------------------
    # User Menu（avatar dropdown）— sidebar feature 用
    # ------------------------------------------------------------------

    def open_user_menu(self):
        """展開 avatar-menu__panel（hover dropdown）。

        QW 無 hamburger 右側 drawer；user menu 是 avatar-trigger hover 後出現的
        .avatar-menu__panel。hover 以 JS dispatchEvent 觸發（mouseenter/mouseover），
        避免 Playwright hover() 後 mouseleave 立即收起。
        等待 .avatar-menu__panel visible 作為展開成功信號。
        """
        self.dismiss_any_popups()
        self.avatar_trigger.evaluate("""el => {
            const rect = el.getBoundingClientRect();
            const opts = { bubbles: true, cancelable: true,
                clientX: rect.left + rect.width / 2, clientY: rect.top + rect.height / 2 };
            el.dispatchEvent(new MouseEvent('mouseenter', opts));
            el.dispatchEvent(new MouseEvent('mouseover', opts));
        }""")
        expect(self.page.locator('.avatar-menu__panel')).to_be_visible(timeout=5000)

    def user_menu_item_texts(self) -> list:
        """回傳 avatar-menu__panel 內的項目文字（含登出按鈕）。

        供 sidebar feature 驗證選單結構完整性。
        呼叫前須先 open_user_menu()。
        """
        panel = self.page.locator('.avatar-menu__panel')
        return panel.evaluate(
            """el => {
                const out = [];
                el.querySelectorAll('.avatar-menu__item, button').forEach(n => {
                    const t = (n.textContent || '').trim().replace(/\\s+/g, ' ');
                    if (t) out.push(t);
                });
                return out;
            }"""
        )

    # ------------------------------------------------------------------
    # 會員中心 — member feature 用
    # ------------------------------------------------------------------

    def open_member_page(self):
        """開啟會員中心（點 avatar panel 中「帳戶管理」→ /member-center?type=MyAccount）。

        QW 會員中心入口：hover avatar-trigger → panel 展開 → 點「帳戶管理」。
        「帳戶管理」為 .avatar-menu__item 第一項，click 後 URL → /member-center?type=MyAccount。
        probe 確認（2026-06-25）：click（非 dispatch_event）觸發 Vue router。

        注意：go_home 後 Nuxt hydration 需要時間完成；panel visible 不代表 Vue click handler
        已綁定。加短暫 wait 讓 hydration 穩定，避免 click 後 router 不響應。
        本方法只負責觸發動作，不等 navigation；呼叫端需自行等 URL 變更。
        """
        sh = get_screenshotter(self.page)
        self.open_user_menu()
        panel = self.page.locator('.avatar-menu__panel')
        if sh: sh.capture(panel, "verify_panel_opened")
        # 等待 Vue click handler 綁定（panel 可見後短暫 hydration 延遲）
        self.page.wait_for_timeout(500)
        # 點「帳戶管理」（第一個 item，locale 繁體下確認為此文案）
        # 多語系保護：用 first item 定位，不寫死文案
        first_item = panel.locator('.avatar-menu__item').first
        if sh: sh.capture(first_item, "click_帳戶管理")
        first_item.click()

    # ------------------------------------------------------------------
    # 錢包 / 存提 — wallet feature 用
    # ------------------------------------------------------------------

    def wallet_shortcut_tiles(self):
        """回傳首頁 shortcut-tile 連結清單（locator list）。

        QW 首頁 nav 區右側有 3 個 a.shortcut-tile：
          存款 → /member-center?type=Deposit
          轉帳 → /member-center?type=GameWallets
          取款 → /member-center?type=Withdrawal
        probe 確認（2026-06-25）：真實 <a href> 連結，非 JS handler。
        """
        return self.page.locator('a.shortcut-tile')

    def click_shortcut_tile(self, type_key: str):
        """點首頁 shortcut-tile（存款/轉帳/取款）並等待 URL 跳轉至 /member-center?type=<key>。

        type_key 對應 URL query：Deposit / GameWallets / Withdrawal。
        tile 為 <a href='/member-center?type=<key>'> 真實連結，直接 click 觸發導航。
        呼叫端需自行等待 URL 確認後截圖。
        """
        sh = get_screenshotter(self.page)
        tile = self.page.locator(f"a.shortcut-tile[href*='type={type_key}']").first
        tile.scroll_into_view_if_needed()
        if sh: sh.capture(tile, f"click_shortcut_{type_key}")
        tile.click()

    # ------------------------------------------------------------------
    # 遊戲 — game feature 用
    # ------------------------------------------------------------------

    # 首頁遊戲分類 intro-tab（6 個：電子/真人/捕魚/棋牌/體育/彩票）
    # active 狀態含 .intro-tab--active class（probe 2026-06-25）
    INTRO_TAB = ".intro-tab"
    # 提供商 tiles（首頁遊戲 intro 區，DIV，click 後 Nuxt SPA 路由跳轉至分類頁）
    INTRO_PLATFORM = ".intro-platform.group"
    # 遊戲卡（/Categories/slots?gamePlatformId=XXX 頁）
    # probe 確認：grid.grid-cols-8 內 div.group.relative.h-[124px].w-[124px].cursor-pointer
    GAME_CARD = "div.group.relative.h-\\[124px\\].w-\\[124px\\].cursor-pointer"

    def open_slots_category(self):
        """點電子分類的第一個 intro-platform tile → Nuxt 路由至 /Categories/slots?gamePlatformId=XXX。

        QW 不像 KS 有 nav href 直連分類頁；須先滾動到 intro-platform 區再點 tile。
        click 後 URL 包含 /Categories/slots（SPA pushState）且遊戲 grid 渲染。
        呼叫端需自行等 URL 確認後等待遊戲 grid。
        """
        sh = get_screenshotter(self.page)
        self.dismiss_any_popups()
        # 滾動到 intro-platform
        platform = self.page.locator(self.INTRO_PLATFORM).first
        platform.scroll_into_view_if_needed()
        if sh: sh.capture(platform, "click_intro_platform_slots")
        platform.click()

    def game_card_count(self) -> int:
        """遊戲卡 grid 目前可見的卡片數量（進入分類頁後使用）。"""
        return self.page.locator(self.GAME_CARD).count()

    def launch_game(self, index: int = 0):
        """點第 index 張遊戲卡啟動遊戲，回傳另開的遊戲新分頁（已最大化）。

        QW 流程（probe 2026-06-25）：點遊戲卡 → window.open 新分頁 → /launchLoading →
        後端簽發 token 後轉址至第三方 provider。
        dev 環境 launchLoading 未轉址（後端 provider 未完成配置），故 game launch
        測試目前 skip（見 test_game_launch.py）。本方法保留供未來使用。

        新分頁不繼承最大化視窗，故 maximize_page() 校正座標/截圖。
        """
        from utils.window_helper import maximize_page
        sh = get_screenshotter(self.page)
        launcher = self.page.locator(self.GAME_CARD).nth(index)
        launcher.wait_for(state="attached", timeout=20000)
        if sh: sh.full_page(f"click_啟動遊戲_第{index}款")
        with self.page.context.expect_page(timeout=20000) as new_page_info:
            launcher.click()
        game_page = new_page_info.value
        maximize_page(game_page)
        return game_page
