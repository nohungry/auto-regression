"""
首頁 Page Object — lt 站點（desktop responsive 版，2026-05-18 rewrite）

關鍵概念（probe 2026-05-18）：
- 個人中心非獨立路由（無 /member-center）；點底部「個人」tab 在 `/` 開 `.dialog-mask-full` overlay panel
- 登入成功標記：DLT cookie 存在（Nuxt SPA pushState 但 page.url 仍顯示 /login，不可靠）
- Navbar 已登入：信用額度 `.coin-wrap-bg span`、帳號 `.user-info-bg p.tip-single`
- 登出：panel 內的 `button.cancel-btn` filter "登出"，無確認 dialog
- 所有 click 都要 dispatch_event（Vue handler 攔截 + tab 是 div 不是 button）

WAP 時期（2026-04-21）的這些假設已全部失效：
- `.bg-navbar` / `.shadow-menubar` / `.cat-btn` / `.bg-secondary` 都不在了
- `/member-center` 路由不存在
- LaiTsai / userLaiTsai cookie 已改名為 DLT
"""

import time

from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError, expect
from utils.screenshot_helper import get_screenshotter


class HomePage:

    def __init__(self, page: Page):
        self.page = page

        # Navbar
        self.navbar = page.locator(".nav-bg-m").first
        self.navbar_balance = page.locator(".coin-wrap-bg span").first
        # 已登入時顯示 username；保留舊命名 navbar_login_pill 以維持測試介面相容
        self.navbar_login_pill = page.locator(".user-info-bg p.tip-single").first
        # 未登入時 navbar 右側「登入」CTA
        self.login_cta_btn = page.locator("div.login-btn-with-text").first

        # 底部 tabbar「個人」— tap 後在 / 開 .dialog-mask-full panel
        # 結構性 locale-agnostic：footer 5 個 .content tab，「個人」固定在最後
        # 不用 has_text="個人"（i18n 切換後其他語系命中不到，POM 整個 fail）
        self.bottom_tab_member = page.locator(".footer-bg .content").last

        # Member center overlay panel
        self.member_panel = page.locator(".dialog-mask-full").first
        self.logout_btn = page.locator("button.cancel-btn").filter(has_text="登出").first

    def is_logged_in(self) -> bool:
        """以 DLT cookie 存在判斷登入狀態"""
        for c in self.page.context.cookies():
            if c.get("name") == "DLT" and c.get("value"):
                return True
        return False

    def verify_logged_in(self):
        """斷言已登入：navbar pill 顯示非空帳號文字"""
        sh = get_screenshotter(self.page)
        self.navbar_login_pill.wait_for(state="visible", timeout=10000)
        text = (self.navbar_login_pill.inner_text() or "").strip()
        assert text != "", "navbar login pill 應顯示帳號"
        if sh: sh.capture(self.navbar_login_pill, "verify_已登入_navbar_pill")

    def verify_login_success(self, username: str):
        """驗證登入成功：navbar pill 顯示 username"""
        sh = get_screenshotter(self.page)
        expect(self.navbar_login_pill).to_have_text(username, timeout=10000)
        if sh: sh.capture(self.navbar_login_pill, f"verify_帳號顯示_{username}")

    def dismiss_any_popups(self):
        """LT 無伺服器錯誤 popup；UA / 錯誤 dialog 由 LoginPage 處理"""
        pass

    def open_member_center(self):
        """tap 底部「個人」tab → 開啟 .dialog-mask-full overlay panel（非 navigate）。
        冪等：panel 已開則跳過。
        """
        sh = get_screenshotter(self.page)
        if self.member_panel.is_visible():
            return
        self.bottom_tab_member.wait_for(state="visible", timeout=5000)
        if sh: sh.capture(self.bottom_tab_member, "click_個人tab")
        self.bottom_tab_member.dispatch_event("click")
        self.member_panel.wait_for(state="visible", timeout=8000)

    def logout(self):
        """tap 個人 → tap 登出。無確認 dialog；登出後 DLT cookie 被清除。"""
        sh = get_screenshotter(self.page)
        self.open_member_center()
        self.logout_btn.wait_for(state="visible", timeout=5000)
        if sh: sh.capture(self.logout_btn, "click_登出")
        self.logout_btn.dispatch_event("click")

        # 等 DLT cookie 消失（最多 10s）
        deadline = time.monotonic() + 10
        while time.monotonic() < deadline:
            if not self.is_logged_in():
                break
            time.sleep(0.2)

        # 並等未登入 CTA 出現
        self.login_cta_btn.wait_for(state="visible", timeout=5000)
        if sh: sh.capture(self.login_cta_btn, "verify_登出成功_未登入CTA出現")

    def click_nav_item(self, name: str):
        """舊 .cat-btn 分類 tab 在 2026-05-18 換版已被新版 swipe sections 取代。
        若需點 section title 請改用 `page.locator('span.category-title').filter(has_text=name)`。
        保留簽名僅為防呼叫端 import 錯誤；呼叫會 raise，提示重寫。
        """
        raise NotImplementedError(
            "LT desktop 版已無 .cat-btn 分類；改用 swipe sections (span.category-title)"
        )
