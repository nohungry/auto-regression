"""
首頁 Page Object — qw 站點（LM來財娛樂城）
登入成功後的首頁驗證、彈窗清理、登出

probe 結果（2026-05-22）：
- Avatar：img[alt="avatar"]（與 RC 同 alt，巧合）
- Avatar 容器：.avatar-trigger（cursor-pointer）
- Username 顯示：.avatar-trigger p
- Dropdown：hover 觸發（非 click！Vue/Nuxt behavior）
- 登出按鈕：button.avatar-menu__logout
- 公告彈窗：.popup-mask（全屏 mask）+ .popup-close（X 按鈕）
- TOTP 提示：button，text 含「下次再說」（多語系：用 has_text 配合 try-except）

多語系注意：QW 多語系站（LaiBetLanguage cookie），不綁文案 selector。
登出按鈕用 CSS class（.avatar-menu__logout）而非文案。
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
