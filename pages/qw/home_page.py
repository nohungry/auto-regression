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

        QW 兩種彈窗都用 `.popup-mask` 包覆並會 intercept pointer events：
          1. 公告彈窗（首頁）— `.popup-close` X 按鈕
          2. TOTP 安全中心提示（登入後）— button text=「下次再說」

        策略：loop 最多 3 輪 dismiss，直到 `.popup-mask` 完全消失或 timeout。
        TOTP 提示可能在公告 popup 關掉後才 render，所以單次 dismiss 不夠。
        """
        for _ in range(3):
            # 1. 公告彈窗
            try:
                popup_close = self.page.locator('.popup-close').first
                popup_close.wait_for(state="visible", timeout=1500)
                popup_close.click()
            except PlaywrightTimeoutError:
                pass

            # 2. TOTP 提示（「下次再說」；多語系站台僅繁中模式下 text 如此）
            # TODO: 待主 context probe 確認其他語系的文案後，補充對應文案或改 CSS selector
            try:
                totp_dismiss = self.page.locator('button', has_text="下次再說")
                totp_dismiss.wait_for(state="visible", timeout=1500)
                totp_dismiss.click()
            except PlaywrightTimeoutError:
                pass

            # 檢查所有 .popup-mask 是否都已隱藏，若是則跳出 loop
            try:
                self.page.locator('.popup-mask').first.wait_for(state="hidden", timeout=1000)
                break
            except PlaywrightTimeoutError:
                continue

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
