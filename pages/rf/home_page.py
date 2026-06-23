"""
首頁 Page Object — rf 站點（金爺娛樂城）
登入成功後的首頁驗證、彈窗清理、導覽、登出

probe 結果（dev-rf，2026-06-17）：
- 已登入信號：.info_name（文字 = 帳號名，如「drfauto01」）
- 帳號區下拉觸發：.loginInBox（含 avatar + .info_name + 餘額），點後展開 .user-dropmenu
  備援：點 .loginInBox 內 avatar img（若主觸發點無效）
- 登出鈕：button.btn-logout（在 .user-dropmenu__logout 內）
- 登出後：a.btn-login 重新出現（登入/註冊）
- 導覽：首頁=a.router-link-active；真人/電子/捕魚 為 button（純文字無穩定 class），
  用 text=真人 / text=電子 / text=捕魚 配 .first（文字也出現在遊戲卡，務必 .first）
- base-modal 確定：button.btn-gold；容器：.base-modal__container
"""

from urllib.parse import urlparse
from playwright.sync_api import Page, expect, TimeoutError as PlaywrightTimeoutError
from utils.screenshot_helper import get_screenshotter


class HomePage:

    def __init__(self, page: Page):
        self.page = page

        # 已登入信號：帳號名稱文字（登入後才渲染）
        self.info_name = page.locator(".info_name")

        # 未登入信號 / 登出後驗證：登入入口 <a>
        self.login_btn = page.locator("a.btn-login")

        # 帳號區下拉觸發（含 avatar + info_name + 餘額）
        self.account_box = page.locator(".loginInBox")

        # 使用者下拉選單（登出等入口）
        self.user_dropmenu = page.locator(".user-dropmenu")

        # 登出按鈕（button，在 .user-dropmenu__logout 內）
        self.logout_btn = page.locator("button.btn-logout")

        # 主導覽列容器（首頁/真人/電子/捕魚 button 皆在此 nav 內）。
        # 用於 scope nav 項目，避免 text= 命中首頁遊戲卡上的同名文字（假綠燈）。
        self.nav_menu = page.locator("nav.menu_nav")

        # base-modal 容器（dismiss_any_popups 使用）
        self.modal_container = page.locator(".base-modal__container")

    # ------------------------------------------------------------------
    # 登入狀態驗證
    # ------------------------------------------------------------------

    def is_logged_in(self) -> bool:
        """判斷目前是否已登入（.info_name 可見，timeout 3s，失敗回 False）。"""
        try:
            return self.info_name.is_visible(timeout=3000)
        except PlaywrightTimeoutError:
            return False

    def verify_logged_in(self):
        """輕量驗證：.info_name 可見即代表已登入。無副作用。"""
        sh = get_screenshotter(self.page)
        expect(self.info_name).to_be_visible(timeout=10000)
        self.info_name.scroll_into_view_if_needed()
        if sh:
            sh.capture(self.info_name, "verify_已登入_帳號名稱顯示")

    def verify_login_success(self, username: str):
        """驗證登入成功：.info_name 可見 + 文字含登入帳號。

        斷言策略：
        - .info_name 可見（登入後才渲染，明確的已登入信號）
        - .info_name 文字含 username（驗證正確帳號登入）
        """
        sh = get_screenshotter(self.page)

        expect(self.info_name).to_be_visible(timeout=15000)
        self.info_name.scroll_into_view_if_needed()
        if sh:
            sh.capture(self.info_name, f"verify_帳號名稱_{username}")
        expect(self.info_name).to_contain_text(username, timeout=5000)

    def verify_logged_out(self):
        """驗證已登出：a.btn-login 重新出現。"""
        sh = get_screenshotter(self.page)
        expect(self.login_btn).to_be_visible(timeout=10000)
        self.login_btn.scroll_into_view_if_needed()
        if sh:
            sh.capture(self.login_btn, "verify_已登出_登入按鈕出現")

    # ------------------------------------------------------------------
    # 彈窗清理
    # ------------------------------------------------------------------

    def dismiss_any_popups(self):
        """防禦性清除 base-modal 確定彈窗（最多 3 次 loop）。

        登入後進站公告若以 base-modal 形式出現也會被一併清除。
        只點「確定」(btn-gold)，不點「取消」(btn-cancel)。
        """
        for _ in range(3):
            try:
                self.modal_container.first.wait_for(state="visible", timeout=2000)
            except PlaywrightTimeoutError:
                break
            try:
                btn = self.modal_container.locator("button.btn-gold").first
                btn.wait_for(state="visible", timeout=2000)
                btn.scroll_into_view_if_needed()
                btn.click()
                self.page.wait_for_timeout(500)
            except PlaywrightTimeoutError:
                break

    # ------------------------------------------------------------------
    # 帳號下拉選單
    # ------------------------------------------------------------------

    def open_user_dropdown(self):
        """點 .loginInBox 展開使用者下拉選單 .user-dropmenu。

        備援：若 .user-dropmenu 未出現，改點 .loginInBox 內的 avatar img 再試一次。
        """
        sh = get_screenshotter(self.page)
        self.account_box.scroll_into_view_if_needed()
        if sh:
            sh.capture(self.account_box, "click_帳號區展開下拉")
        self.account_box.click()

        try:
            self.user_dropmenu.wait_for(state="visible", timeout=5000)
        except PlaywrightTimeoutError:
            # 備援：點 .loginInBox 內的 avatar img
            avatar_img = self.account_box.locator("img").first
            avatar_img.scroll_into_view_if_needed()
            avatar_img.click()
            self.user_dropmenu.wait_for(state="visible", timeout=5000)

        if sh:
            sh.capture(self.user_dropmenu, "verify_下拉選單展開")

    # ------------------------------------------------------------------
    # 導覽
    # ------------------------------------------------------------------

    def click_nav_item(self, name: str):
        """點擊導覽列分類項目（真人/電子/捕魚）。

        限縮在 nav.menu_nav 容器內的 button，避免命中首頁遊戲卡上的同名文字。
        真人/電子/捕魚 為 button（純文字無穩定 class），但都在 nav.menu_nav 下。
        """
        sh = get_screenshotter(self.page)
        item = self.nav_menu.locator("button", has_text=name).first
        item.scroll_into_view_if_needed()
        if sh:
            sh.capture(item, f"click_導覽_{name}")
        item.click()

    # ------------------------------------------------------------------
    # 登出
    # ------------------------------------------------------------------

    def logout(self):
        """登出：點 .loginInBox 展開下拉 → 點 button.btn-logout → 驗證 a.btn-login 出現。"""
        sh = get_screenshotter(self.page)

        # 清除可能殘留的 base-modal（避免擋住操作）
        self.dismiss_any_popups()

        # 展開下拉選單
        self.open_user_dropdown()

        # 點登出
        self.logout_btn.scroll_into_view_if_needed()
        if sh:
            sh.capture(self.logout_btn, "click_登出")
        self.logout_btn.click()

        # 驗證登出成功：登入 CTA 重現
        expect(self.login_btn).to_be_visible(timeout=10000)
        self.login_btn.scroll_into_view_if_needed()
        if sh:
            sh.capture(self.login_btn, "verify_登出成功_登入按鈕出現")

    # ------------------------------------------------------------------
    # 帳戶設定 modal（member 功能）
    # ------------------------------------------------------------------

    def open_account_settings(self):
        """展開 dropmenu → 點「修改資料」打開帳戶設定 modal（.base-modal.account-settings-modal）。

        probe 結果：
        - dropmenu 內只有「修改資料」（nth 0）和「會員訊息」（nth 1）兩項，
          都會打開同一個「帳戶設定」modal。
        - modal 打開後 .loginInBox 被 pointer-events 攔截，必須先關閉 modal 才能再點 loginInBox。
        """
        sh = get_screenshotter(self.page)
        self.open_user_dropdown()
        modify_item = self.user_dropmenu.locator(".user-dropmenu__item").nth(0)
        modify_item.scroll_into_view_if_needed()
        if sh:
            sh.capture(modify_item, "click_修改資料")
        modify_item.click()
        # 等 modal 容器出現
        self.modal_container.wait_for(state="visible", timeout=8000)
        if sh:
            sh.full_page("verify_帳戶設定modal開啟")

    def close_account_settings(self):
        """關閉帳戶設定 modal（Escape 鍵，無關閉按鈕 selector）。

        關閉後需等 modal 消失才可再操作 .loginInBox。
        """
        self.page.keyboard.press("Escape")
        try:
            self.modal_container.wait_for(state="hidden", timeout=5000)
        except PlaywrightTimeoutError:
            pass

    def get_profile_account_name(self) -> str:
        """從帳戶設定 modal 的 .account-settings__profile 取帳號名文字。

        需在 open_account_settings() 呼叫後使用。
        selector: .account-settings__profile dd（第一個 dd = 會員帳號值）。
        """
        dd = self.modal_container.locator(".account-settings__profile dd").first
        dd.wait_for(state="visible", timeout=5000)
        return dd.inner_text().strip()

    def get_modal_balance_text(self) -> str:
        """從帳戶設定 modal 的 .account-settings__balance 取餘額文字（純數值如 10,000.00）。

        使用 evaluate 取 text nodes（排除 SVG 內容）。
        需在 open_account_settings() 呼叫後使用。
        """
        balance_el = self.modal_container.locator(".account-settings__balance")
        balance_el.wait_for(state="visible", timeout=5000)
        text = self.page.evaluate("""() => {
            const bal = document.querySelector('.account-settings__balance');
            if (!bal) return '';
            const walker = document.createTreeWalker(bal, NodeFilter.SHOW_TEXT);
            let node, texts = [];
            while(node = walker.nextNode()) {
                const t = node.textContent.trim();
                if (t) texts.push(t);
            }
            return texts.join(' ').trim();
        }""")
        return text

    def click_member_menu_tab(self, tab_index: int):
        """點帳戶設定 modal 側邊欄的 tab 按鈕（0=修改密碼，1=會員訊息）。

        使用 modal 容器內的 .account-settings-menu__item 限縮範圍，
        避免點擊後 DOM 重組造成 strict mode 問題。
        """
        sh = get_screenshotter(self.page)
        tab_btn = self.modal_container.locator(".account-settings-menu__item").nth(tab_index)
        tab_btn.scroll_into_view_if_needed()
        if sh:
            sh.capture(tab_btn, f"click_設定tab_{tab_index}")
        tab_btn.click()
        # 等主面板出現
        self.modal_container.locator(".account-settings__main").wait_for(state="visible", timeout=5000)
        if sh:
            sh.full_page(f"verify_設定tab_{tab_index}_已切換")

    def get_inbox_state_text(self) -> str:
        """從「會員訊息」tab 取狀態文字（如「目前沒有訊息」）。

        需在 click_member_menu_tab(1) 後使用。
        selector: .account-settings-messages__state
        """
        state_el = self.modal_container.locator(".account-settings-messages__state")
        state_el.wait_for(state="visible", timeout=5000)
        return state_el.inner_text().strip()

    # ------------------------------------------------------------------
    # wallet（首頁餘額）
    # ------------------------------------------------------------------

    def get_navbar_balance_text(self) -> str:
        """取首頁 navbar 的餘額文字（.loginInBox .coin span）。

        斷言策略：只驗非空 + 格式含數字，不寫死特定金額。
        """
        sh = get_screenshotter(self.page)
        coin_span = self.account_box.locator(".coin span")
        expect(coin_span).to_be_visible(timeout=10000)
        coin_span.scroll_into_view_if_needed()
        text = coin_span.inner_text().strip()
        if sh:
            sh.capture(coin_span, f"verify_navbar信用額度非空_{text}")
        return text

    # ------------------------------------------------------------------
    # 遊戲啟動（game feature 使用）
    # ------------------------------------------------------------------

    def open_slots_category(self):
        """導航至電子(slots)分類頁並等遊戲卡 grid 渲染。

        RF 遊戲分類頁路徑：/Categories/slots
        遊戲卡 selector：.gameShowcaseSection__card（probe 2026-06-17 確認）
        dev 環境可能延遲渲染，用 wait_for(attached, 15s) 等第一張卡。
        """
        sh = get_screenshotter(self.page)
        self.dismiss_any_popups()
        parsed = urlparse(self.page.url)
        base = f"{parsed.scheme}://{parsed.netloc}"
        self.page.goto(
            base + "/Categories/slots",
            wait_until="domcontentloaded",
            timeout=30000,
        )
        self.page.wait_for_timeout(1500)
        if sh:
            sh.full_page("verify_slots分類頁載入")
        # 等第一張卡出現（attached 不要求 visible，dev 環境慢）
        first_card = self.page.locator(".gameShowcaseSection__card").first
        first_card.wait_for(state="attached", timeout=15000)

    def game_card_count(self) -> int:
        """目前分類頁遊戲卡數量（.gameShowcaseSection__card）。"""
        return self.page.locator(".gameShowcaseSection__card").count()

    def launch_game(self, index: int = 0) -> str:
        """點第 index 張遊戲卡，等待同頁路由至 /Game，回傳最終 URL。

        RF 遊戲行為（probe 2026-06-17）：
        - 點 .gameShowcaseSection__card → 同頁路由至 /Game?gamePlatformId=...&gameId=...
        - 不開新分頁（window.open 未觸發）
        - /Game 頁有 iframe.game-iframe，dev 環境 src 可能為空（staging 遊戲不一定載入）
        - 故只驗「URL 已切換到 /Game」，不等 iframe src 外部 provider
        """
        sh = get_screenshotter(self.page)
        card = self.page.locator(".gameShowcaseSection__card").nth(index)
        card.wait_for(state="attached", timeout=15000)
        if sh:
            sh.full_page(f"click_啟動遊戲_第{index}張卡")
        card.click()
        # 等同頁路由完成：URL 含 /Game
        self.page.wait_for_url(lambda url: "/Game" in url, timeout=15000)
        return self.page.url

    # ------------------------------------------------------------------
    # i18n（語言切換）
    # ------------------------------------------------------------------

    def get_lang_cookie(self) -> str:
        """取目前語系 cookie（i18n_locale）值。

        RF 使用 i18n_locale（非 i18n_redirected），預設值為 'tw'（繁體中文）。
        """
        cookies = {c["name"]: c["value"] for c in self.page.context.cookies()}
        return cookies.get("i18n_locale", "")

    def open_lang_selector(self):
        """點 .lang-selector button.btn-icon 展開語言選單（.lang-selector__list）。

        probe 2026-06-17：
        - .lang-selector 為常駐可見 globe icon（w=48, h=28）
        - 點 button.btn-icon 展開 __list（5 語系 LI 項）
        - __list 在未展開狀態下不可見（CSS display:none 或 visibility）
        """
        sh = get_screenshotter(self.page)
        btn = self.page.locator(".lang-selector button.btn-icon")
        btn.scroll_into_view_if_needed()
        if sh:
            sh.capture(btn, "click_語言選擇器開啟")
        btn.click()
        # 等 list 出現（以第一個 li 判斷）
        first_li = self.page.locator(".lang-selector__list li").first
        first_li.wait_for(state="visible", timeout=5000)
        if sh:
            sh.capture(self.page.locator(".lang-selector__list"), "verify_語言選單展開")

    def switch_language(self, lang_text: str):
        """點語言切換選單中的指定語系 li，等待 i18n_locale cookie 更新。

        Args:
            lang_text: 選單 li 文字，如 'English'、'繁體中文'、'简体中文'

        probe 2026-06-17：
        - .lang-selector__list li 有 5 個，文字分別為：
          繁體中文 / 简体中文 / English / Tiếng Việt / ภาษาไทย
        - 目前 active 項有 class="active"（繁體中文為 active）
        - 點擊後頁面 nav 文案同步更新，i18n_locale cookie 更新（tw/cn/en/vi/th）
        - __list li 的 inner_text() 在 headless 模式下回空字串；
          需用 has_text 過濾或 nth() 定位
        """
        sh = get_screenshotter(self.page)
        target = self.page.locator(".lang-selector__list li").filter(has_text=lang_text).first
        target.scroll_into_view_if_needed()
        if sh:
            sh.capture(target, f"click_語言切換_{lang_text}")
        target.click()
        # 等待頁面語系更新（nav 文案變動或 cookie 更新）
        self.page.wait_for_timeout(1500)
