"""
後台管理頁 Page Object — LU 站點（Dlu測試站）

範圍：read-only 導航 + logout（不含存提）。同時支援站長與代理兩種帳號層級。

實機 probe 關鍵事實：

站長層級（<LU 站長帳號>，2026-06-12）：
- 側欄容器 class 為 `.sidebar hide`（收合/移出畫面）→ 側欄連結永遠在 viewport 外，
  **必須用 `dispatch_event("click")`**（仿 RC CSS-hidden sidebar 慣例，見 CLAUDE.md）。
- 頂層選單 `.sidebar-nav li.parent-li`（18 項）；父項錨點 `a.memberSpan` 帶 `id`=route
  （如 `id="/member"`）。葉節點 `a[href^='#/...']`（如 `#/member/member-registration`）
  即使側欄收合仍在 DOM，可直接 dispatch 導航 → 用 `navigate(route_substr)`。

代理層級（<LU 代理帳號>，2026-06-15）：
- 側欄可見（class `sidebar`，非 `sidebar hide`）；頂層選單僅 **5 項**
  （/member、/agent、/report、/report-bet-count、/statistical-report）。
- 子選單預設收合，需先點父項展開（`div.collapse` 加 `.show`）；
  **葉節點無 href**（`li > a > div.collapse-li-text`，Vue @click 導航）→ 用 `navigate_agent(parent_id)`。

共用：
- 內容載入信號：`.app-main-content` 容器。
- 右上 `.user-account`（顯示帳號）點擊開下拉選單 → 含 `Reset Password / Wallet /
  Agent Information / Logout`；Logout 為 `a` 文字連結（英文後台；locale 切換時文案會變，
  目前 admin 預設英文，與登入鈕 "Login" 一致採文字定位）。
"""

from playwright.sync_api import Page
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

from utils.screenshot_helper import get_screenshotter

# 主錢包額度調整模式 → Deposit/Withdrawal select 的 option value（實機 probe 2026-06-25）
WALLET_ADJUST_MODES = {
    "increase": "1",  # Amount adjustment increased（額度調整-增加）
    "reduce": "2",    # Amount adjustment reduce（額度調整-減少）
    "deposit": "3",   # General deposit（一般存款，會帶出 Platform/Member bank 欄）
}


def _parse_amount(text: str) -> float:
    """'1,000' / ' 1,001 ' → 1000.0 / 1001.0（去千分位逗號與空白）。"""
    return float(text.replace(",", "").strip())


class ManagementPage:

    def __init__(self, page: Page):
        self.page = page
        self.sidebar = page.locator(".sidebar-nav")
        self.parent_items = page.locator(".sidebar-nav li.parent-li")
        self.content = page.locator(".app-main-content")
        self.user_account = page.locator(".user-account").first
        self.logout_link = page.get_by_role("link", name="Logout")
        # 主錢包充值彈窗（站長層級；代理點金額不會開此彈窗）
        self.wallet_dialog = page.locator(".dialog-container").first

    def sidebar_item_count(self) -> int:
        """頂層選單（li.parent-li）數量；先等側欄掛上 DOM。"""
        self.sidebar.first.wait_for(state="attached", timeout=15000)
        return self.parent_items.count()

    def parent_route_ids(self) -> list:
        """回傳頂層選單的 route id 清單（父項 `a.memberSpan` 的 id，如 '/member'）。
        locale-agnostic：id 是 route 不是文案，可穩定比對權限/可見選單。
        """
        self.sidebar.first.wait_for(state="attached", timeout=15000)
        spans = self.page.locator(".sidebar-nav li.parent-li a.memberSpan")
        return [spans.nth(i).get_attribute("id") for i in range(spans.count())]

    def navigate(self, route_substr: str):
        """（站長層級）點側欄葉節點導航到含 route_substr 的頁面。
        側欄 .sidebar.hide 收合 → 連結在 viewport 外，必須 dispatch_event("click")。
        站長葉節點為 `a[href^='#/...']`（即使收合仍在 DOM）。
        以 URL hash 變化 + 內容容器可見作為導航成功判定（結構性，不綁文案）。
        """
        sh = get_screenshotter(self.page)
        link = self.page.locator(f"a[href*='{route_substr}']").first
        link.wait_for(state="attached", timeout=10000)
        link.dispatch_event("click")
        self.page.wait_for_url(f"**{route_substr}**", timeout=15000)
        self.content.first.wait_for(state="visible", timeout=15000)
        if sh:
            sh.full_page(f"verify_導航_{route_substr.replace('/', '_')}")

    def navigate_agent(self, parent_id: str, leaf_index: int = 0):
        """（代理層級）展開父選單 → 點葉節點導航。回傳導航後 URL。

        代理側欄與站長不同（2026-06-15 probe）：
        - 側欄可見（class `sidebar`，非 `sidebar hide`）。
        - 子選單預設收合，需先點父項 `a.memberSpan[id=parent_id]`（如 `/member`）展開
          （展開後 `div.collapse` 加上 `.show`）。
        - **葉節點無 href**（Vue @click 程式化導航），故用結構定位
          `li.parent-li:has(a.memberSpan[id=parent_id]) div.collapse a`，
          不能沿用站長的 `a[href*=...]`。

        導航判定：URL 含父項 route 段（parent_id）+ 內容容器可見（結構性，不綁文案）。
        """
        sh = get_screenshotter(self.page)
        parent = self.page.locator(f"a.memberSpan[id='{parent_id}']").first
        parent.wait_for(state="attached", timeout=10000)
        parent.dispatch_event("click")  # 展開子選單

        leaf = self.page.locator(
            f"li.parent-li:has(a.memberSpan[id='{parent_id}']) div.collapse a"
        ).nth(leaf_index)
        leaf.wait_for(state="attached", timeout=10000)
        leaf.dispatch_event("click")

        # parent_id 形如 '/member'；導航後 URL hash 應含該段
        self.page.wait_for_url(f"**{parent_id}/**", timeout=15000)
        self.content.first.wait_for(state="visible", timeout=15000)
        if sh:
            sh.full_page(f"verify_代理導航_{parent_id.strip('/').replace('/', '_')}")
        return self.page.url

    def open_user_menu(self):
        """點右上使用者帳號開下拉選單（含 Logout）。"""
        sh = get_screenshotter(self.page)
        self.user_account.click()
        self.logout_link.wait_for(state="visible", timeout=8000)
        if sh:
            sh.capture(self.user_account, "click_使用者選單")

    def logout(self):
        """登出 → 回 #/login（登入表單重現）。"""
        sh = get_screenshotter(self.page)
        self.open_user_menu()
        if sh:
            sh.capture(self.logout_link, "click_登出")
        self.logout_link.click()
        self.page.wait_for_url("**/login**", timeout=15000)
        self.page.locator("input[type='password']").first.wait_for(state="visible", timeout=15000)
        if sh:
            sh.full_page("verify_登出回登入頁")

    # ------------------------------------------------------------------
    # 站長：會員主錢包額度調整（測試專用充值路徑，非正規金流）
    #
    # 路徑：會員管理頁 → 搜尋會員 → Main wallet 欄點金額（div.bold）→ 開「Main wallet」
    # 彈窗 → 選 增加/減少 → 填 Amount → Confirm。實機 probe（2026-06-25）：
    # 此能力站長專屬，代理點金額不會開彈窗（Game wallet/Send points 亦 disabled）。
    # 對稱可逆：增加 N → 驗 +N → 減少 N 還原。
    # ------------------------------------------------------------------

    def goto_member_management(self, base_url: str):
        """前往會員管理頁（站長）。Vue SPA 不可用 networkidle。"""
        self.page.goto(
            f"{base_url}#/member/member-management", wait_until="domcontentloaded"
        )
        self.sidebar.first.wait_for(state="attached", timeout=15000)
        self.content.first.wait_for(state="visible", timeout=15000)

    def search_member(self, username: str):
        """於搜尋框填入會員帳號 → Search → 等該會員列出現。

        搜尋區第一個 text input 即 Member 欄（前面的 checkbox 是 Fuzzy search，
        已被 input[type='text'] 過濾掉）。預設不帶條件不載入資料，故必須按 Search。
        """
        sh = get_screenshotter(self.page)
        inp = self.content.locator("input[type='text']").first
        inp.wait_for(state="visible", timeout=10000)
        inp.fill(username)
        if sh:
            sh.capture(inp, f"fill_搜尋會員_{username}")
        self.page.get_by_role("button", name="Search").first.click()
        self._member_row(username).wait_for(state="visible", timeout=10000)
        if sh:
            sh.full_page(f"verify_搜到會員_{username}")

    def _member_row(self, username: str):
        return self.page.locator(f"table tbody tr:has-text('{username}')").first

    def _wallet_amount_locator(self, username: str):
        """主錢包金額元素 = 該會員列中「含 Game wallet 按鈕的 td」內的 div.bold。

        用內容定位而非欄位 index：KS 後台 Main wallet 在 td index 4、LU/LG/QW 在 5，
        且 KS tbody/thead 欄位未對齊（Convenience Store 的 Create cell 會誤命中固定 index）。
        含「Game wallet」按鈕的 cell 是跨站一致的主錢包欄特徵（與旁邊 Send points 同組）。
        （英文後台文案；與既有 get_by_role button "Search"/"Login" 一致採英文定位。）
        """
        return self._member_row(username).locator(
            "td:has(button:has-text('Game wallet')) div.bold"
        ).first

    def get_member_wallet_amount(self, username: str) -> float:
        """讀取會員列 Main wallet 欄顯示金額（內容定位的 div.bold）。"""
        return _parse_amount(self._wallet_amount_locator(username).inner_text())

    def open_main_wallet_dialog(self, username: str):
        """點該會員 Main wallet 金額 → 開「Main wallet」彈窗。"""
        sh = get_screenshotter(self.page)
        amount = self._wallet_amount_locator(username)
        amount.scroll_into_view_if_needed()
        if sh:
            sh.capture(amount, "click_主錢包金額")
        amount.click()
        self.wallet_dialog.wait_for(state="visible", timeout=10000)
        if sh:
            sh.capture(self.wallet_dialog, "verify_主錢包彈窗開啟")

    def dialog_balance(self) -> float:
        """讀彈窗內 Balance（現有餘額）欄；disabled inputs：[0]=Member、[1]=Balance。"""
        return _parse_amount(self.wallet_dialog.locator("input[disabled]").nth(1).input_value())

    def adjust_main_wallet(self, mode: str, amount, remark: str = ""):
        """於已開啟的彈窗執行額度調整：選 mode（increase/reduce/deposit）→ 填 Amount
        → 填 Remark（選填）→ Confirm → 等彈窗關閉。
        """
        sh = get_screenshotter(self.page)
        dlg = self.wallet_dialog
        dlg.locator("select").first.select_option(value=WALLET_ADJUST_MODES[mode])
        amount_input = dlg.locator("input[type='number']")
        amount_input.fill(str(amount))
        if remark:
            dlg.locator("textarea").fill(remark)
        if sh:
            sh.capture(dlg, f"fill_額度調整_{mode}_{amount}")
        dlg.locator("button.confirm-btn").click()
        # Confirm 後彈窗關閉（若站點有二次確認，會在此 timeout，屆時再補處理）
        self.wallet_dialog.wait_for(state="hidden", timeout=15000)
        if sh:
            sh.full_page(f"verify_額度調整完成_{mode}_{amount}")

    # ------------------------------------------------------------------
    # 站長：額度歷史（會員報表 > Amount adjustment）— 驗證充值產生對應稽核紀錄
    #
    # route: #/report/balance-adjustment-report（實機 probe 2026-06-25）
    # 欄位：[0]Member [1]Tag [2]Adjustment type [3]Starting balance [4]Amount
    #       [5]Ending balance [6]Remark [7]Administrator [8]Processing date
    # 預設依 Processing date 由新到舊；增/減各產生一筆 increased/reduced 紀錄。
    # ------------------------------------------------------------------

    def goto_balance_adjustment_report(self, base_url: str):
        """前往額度歷史頁；若有 Search 鈕則按一次確保載入近期紀錄。

        元件 mount 後會跑預設查詢，但若 Search 點太早會在 filter/結果回填前送出，
        導致剛產生的紀錄查不到 → goto 後與 Search 後各加 settle，並等表格有列。
        """
        self.page.goto(
            f"{base_url}#/report/balance-adjustment-report",
            wait_until="domcontentloaded",
        )
        self.sidebar.first.wait_for(state="attached", timeout=15000)
        self.content.first.wait_for(state="visible", timeout=15000)
        self.page.wait_for_timeout(1500)  # 等元件 mount + 預設查詢
        search = self.page.get_by_role("button", name="Search").first
        if search.count():
            search.click()
        self.page.wait_for_timeout(1500)  # 等查詢結果回填表格
        self.page.locator("table tbody tr").first.wait_for(state="visible", timeout=15000)

    def get_adjustment_record(self, remark: str, timeout: int = 8000) -> dict | None:
        """以 Remark 鎖定額度歷史紀錄，回傳 {member, type, amount, end_balance, remark}；無則 None。
        remark 應為呼叫端產生的唯一 token，避免命中歷史殘留的同文案紀錄。
        以等待該列出現（timeout）容忍報表渲染延遲；逾時視為查無。
        """
        row = self.page.locator(f"table tbody tr:has-text('{remark}')").first
        try:
            row.wait_for(state="visible", timeout=timeout)
        except PlaywrightTimeoutError:
            return None
        c = row.locator("td")
        return {
            "member": c.nth(0).inner_text().strip(),
            "type": c.nth(2).inner_text().strip(),
            "amount": _parse_amount(c.nth(4).inner_text()),
            "end_balance": _parse_amount(c.nth(5).inner_text()),
            "remark": c.nth(6).inner_text().strip(),
        }
