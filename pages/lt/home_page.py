"""
首頁 Page Object — lt 站點（LM來財信用網；2026-09-13 rewrite，第三次換版）

dev-lt 自 2026-07-23 起改用與 RC（王老吉）相同的前台模板，本檔依 2026-09-13 實機
probe 重寫（probe 筆記：dev-notes/lt-redesign-v3-probe-2026-09-13.md）。

新版關鍵事實：
- 進站公告＝RC 型 `.popup-announcement-mask`（不清會全屏攔截點擊），
  用 utils.dialog_helper.dismiss_announcement_popup_if_present() 的 CSS killer 清除
- navbar（`.nav-bg`）已登入時顯示：帳號 `p.name-shadow`、信用額度 `.coin-wrap-bg span`、
  頭像 `img[alt="avatar"]`（容器 `.avatar-bg`）；未登入時顯示 `button.nav-login-btn`
- 登出：click `.avatar-bg` 展開帳號下拉（預設 display:none，hover 無效）→ 下拉內唯一 button
- 個人中心＝側欄 `.sidebar-item.user` → 開 `.dialog-mask` + `.dialog-container` 彈窗
  （欄位：帳號 / 暱稱 / 密碼 / 餘額封頂 / 真人限紅，另含 `button.dark-red-btn` 登出）
- `.sidebar-item` 容器 `.sidebar-wrap` 寬度為 0＝永遠在 viewport 外，**必須 dispatch_event("click")**
- 導覽列 `ul.nav-item`，各項以 href 識別（`/Categories/<cat>#gameListSection`），
  文案（真人/電子/…）會隨語系變，一律不綁文字
- 登入態標記仍為 DLT cookie

2026-05-18 desktop responsive 版的假設已全部失效：`.nav-bg-m`、`.user-info-bg`、
`.footer-bg .content` 底部 tabbar、`.dialog-mask-full` overlay panel、`span.category-title`。
"""

from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError, expect
from utils.dialog_helper import (
    dismiss_announcement_popup_if_present,
    dismiss_server_error_if_present,
)
from utils.screenshot_helper import get_screenshotter


# 導覽列項目 → route 片段（locale-agnostic：文案會隨語系變，href 不會）
NAV_ROUTES = {
    "首頁": "/",
    "真人": "/Categories/casino",
    "電子": "/Categories/slots",
    "體育": "/Categories/sports",
    "彩票": "/Categories/lottery",
    "捕魚": "/Categories/fishing",
    "小遊戲": "/Categories/mini-game",
}


class HomePage:

    def __init__(self, page: Page):
        self.page = page

        # Navbar
        self.navbar = page.locator(".nav-bg").first
        self.avatar = page.locator("img[alt='avatar']").first
        self.avatar_btn = page.locator(".avatar-bg").first
        self.navbar_balance = page.locator(".coin-wrap-bg span").first
        # 已登入時 navbar 顯示的帳號文字（保留舊命名以維持呼叫端相容）
        self.navbar_login_pill = page.locator("p.name-shadow").first
        # 未登入時 navbar 右側「登入」CTA
        self.login_cta_btn = page.locator("button.nav-login-btn").first

        # 帳號下拉（含 修改資料 / 會員訊息 / 登出）；結構性定位，不綁文案
        self.user_dropdown = page.locator("div:has(> div.items-container)").first
        self.logout_btn = page.locator("div:has(> div.items-container) > button").first

        # 個人中心：側欄入口 + 彈窗
        self.member_entry = page.locator(".sidebar-item.user").first
        self.member_panel = page.locator(".dialog-mask").first
        self.member_panel_container = page.locator(".dialog-container").first
        self.member_panel_close_btn = page.locator(".dialog-container img[alt='close']").first
        # 彈窗內第一個欄位＝帳號（disabled input，value 為登入帳號）
        self.member_account_input = page.locator(
            ".dialog-container .input-container input.input-style"
        ).first
        # 彈窗底部登出鈕（與 navbar 下拉登出為兩個不同入口）
        self.member_panel_logout_btn = page.locator(".dialog-container button.dark-red-btn").first

    # ── 登入態 ──────────────────────────────────────────────

    def is_logged_in(self) -> bool:
        """以 DLT cookie 存在判斷登入狀態（登出後該 cookie 會被清除）。"""
        for c in self.page.context.cookies():
            if c.get("name") == "DLT" and c.get("value"):
                return True
        return False

    def verify_logged_in(self):
        """輕量驗證：navbar 頭像可見即代表已登入。無副作用。"""
        sh = get_screenshotter(self.page)
        expect(self.avatar).to_be_visible(timeout=15000)
        if sh: sh.capture(self.avatar, "verify_已登入_頭像")

    def verify_login_success(self, username: str):
        """完整驗證：navbar 帳號文字等於登入帳號。"""
        sh = get_screenshotter(self.page)
        expect(self.navbar_login_pill).to_have_text(username, timeout=15000)
        if sh: sh.capture(self.navbar_login_pill, f"verify_navbar帳號_{username}")

    def verify_username_in_drawer(self, username: str):
        """開個人資訊彈窗驗帳號欄＝登入帳號，驗完關閉（副作用較大，只在需要時用）。"""
        sh = get_screenshotter(self.page)
        self.open_member_center()
        expect(self.member_account_input).to_have_value(username, timeout=10000)
        if sh: sh.capture(self.member_account_input, f"verify_個人資訊帳號欄_{username}")
        self.close_member_center()

    # ── 彈窗 ────────────────────────────────────────────────

    def dismiss_any_popups(self):
        """清進站公告（`.popup-announcement-mask`）與伺服器錯誤彈窗。"""
        dismiss_server_error_if_present(self.page)
        dismiss_announcement_popup_if_present(self.page)

    # ── 互動 ────────────────────────────────────────────────

    def open_user_dropdown(self):
        """click 頭像展開帳號下拉（預設 display:none；hover 不會展開）。冪等。"""
        sh = get_screenshotter(self.page)
        if self.logout_btn.is_visible():
            return
        self.dismiss_any_popups()
        self.avatar_btn.wait_for(state="visible", timeout=10000)
        self.avatar_btn.scroll_into_view_if_needed()
        if sh: sh.capture(self.avatar_btn, "click_頭像開啟帳號下拉")
        self.avatar_btn.click()
        self.logout_btn.wait_for(state="visible", timeout=8000)

    def open_member_center(self):
        """開個人資訊彈窗（側欄 `.sidebar-item.user`）。冪等：已開則跳過。

        側欄容器寬度為 0，元素永遠在 viewport 外 → 必須 dispatch_event("click")
        （與 RC `.sidebar-item.*` 同一已知例外，見 CLAUDE.md）。
        """
        sh = get_screenshotter(self.page)
        if self.member_panel.count() > 0 and self.member_panel.is_visible():
            return
        self.dismiss_any_popups()
        self.member_entry.wait_for(state="visible", timeout=10000)
        # 側欄寬度為 0，元素座標永遠落在視窗外 → 紅框圈不到，改存全頁截圖當證據
        if sh: sh.full_page("click_側欄個人資訊")
        self.member_entry.dispatch_event("click")
        self.member_panel.wait_for(state="visible", timeout=10000)
        self.member_account_input.wait_for(state="visible", timeout=10000)

    def close_member_center(self):
        """關閉個人資訊彈窗（右上 close）。未開啟則為 no-op。"""
        if self.member_panel.count() == 0 or not self.member_panel.is_visible():
            return
        self.member_panel_close_btn.click()
        try:
            self.member_panel.wait_for(state="hidden", timeout=5000)
        except PlaywrightTimeoutError:
            pass

    def click_nav_item(self, name: str):
        """點 navbar 導覽項（真人 / 電子 / 體育 / 彩票 / 捕魚 / 小遊戲 / 首頁）。

        以 href 定位（locale-agnostic），文案隨語系變動不影響。
        未知項目直接 raise ValueError，避免無聲點錯。
        """
        route = NAV_ROUTES.get(name)
        if route is None:
            raise ValueError(
                f"未知導覽項目：{name}；可用項目：{', '.join(NAV_ROUTES)}"
            )
        sh = get_screenshotter(self.page)
        self.dismiss_any_popups()
        nav = self.page.locator(f"ul.nav-item a[href^='{route}']").first
        nav.wait_for(state="visible", timeout=10000)
        nav.scroll_into_view_if_needed()
        if sh: sh.capture(nav, f"click_導覽_{name}")
        nav.click()
        try:
            self.page.wait_for_load_state("networkidle", timeout=10000)
        except PlaywrightTimeoutError:
            pass

    def logout(self):
        """登出：頭像下拉 → 登出。登出後停在首頁，DLT cookie 被清除、登入 CTA 再現。"""
        sh = get_screenshotter(self.page)
        self.open_user_dropdown()
        self.logout_btn.scroll_into_view_if_needed()
        if sh: sh.capture(self.logout_btn, "click_登出")
        self.logout_btn.click()
        self.login_cta_btn.wait_for(state="visible", timeout=15000)
        if sh: sh.capture(self.login_cta_btn, "verify_登出完成_登入CTA再現")
