"""
後台管理頁面 Page Object — RC 站點
處理：Tab 切換（代理/會員/子帳號）、代理樹導航、會員存入/提取操作

Tab 定位策略：
  頁面有兩組同名 `button.tab-btn`：
    - sidebar：在 `.tabs-search` 容器
    - 主內容區：在 `.container-management` 容器
  用 `.container-management` 正向 scope 取得主內容區 tab，
  不依賴 DOM 順序的 `.nth()`。

代理樹節點在 overflow 滾動容器中，DOM 存在但可能 hidden，
需使用 JS click 或 dispatch_event 點擊。
"""

import re
from typing import Optional
from playwright.sync_api import Page, Locator, expect, TimeoutError as PlaywrightTimeoutError
from utils.screenshot_helper import get_screenshotter
from utils.dashboard_helpers import sidebar_menu_tree
from utils.wait_helpers import wait_for_text_matches


class ManagementPage:

    def __init__(self, page: Page):
        self.page = page

        # 主內容區容器 — 用於 scope tab buttons，避免誤中 sidebar 同名按鈕
        self._main_content = page.locator('.container-management')

        # 主內容區的 Tab buttons（透過 container scope 限定，不依賴 .nth() 順序）
        self.agent_tab = self._main_content.locator('button.tab-btn', has_text='代理')
        self.member_tab = self._main_content.locator('button.tab-btn', has_text='會員')
        self.sub_account_tab = self._main_content.locator('button.tab-btn', has_text='子帳號')

        # 側欄（入口檢測用）：信用版 /management 後台側欄結構同 RF
        #（.sidebar-nav li.parent-li，父項 a.memberSpan 帶 route id，子入口 li a[href]）
        self.sidebar = page.locator(".sidebar-nav")

    def menu_tree(self) -> list:
        """回傳側欄選單樹 [(parent_route_id, [子入口 href, ...]), ...]（依側欄順序）。

        入口檢測用：與 per-site 預期 spec 精確比對。id/href 為結構性識別，
        不綁文案；'' id = 非路由項目（修改密碼/登出）。實作見
        utils.dashboard_helpers.sidebar_menu_tree（信用版全家共用）。
        """
        tree = sidebar_menu_tree(self.page)
        sh = get_screenshotter(self.page)
        if sh:
            sh.full_page("verify_側欄選單樹")
        return tree

    def get_agent_remaining_balance(self) -> float:
        """
        讀取當前代理的剩餘額度（頁面頂部資訊區）。
        HTML 結構：
          <p class="info-title">剩餘額度</p>
          <p class="info-value">991</p>
        """
        sh = get_screenshotter(self.page)

        title = self.page.locator('p.info-title', has_text='剩餘額度').first
        title.wait_for(state="attached", timeout=5000)

        # 取同層的下一個 sibling（info-value）
        value_el = title.locator('xpath=following-sibling::p[contains(@class,"info-value")]').first
        value_text = value_el.inner_text(timeout=3000)

        balance = float(value_text.strip().replace(',', ''))

        if sh:
            sh.full_page(f"verify_代理剩餘額度_{balance}")

        return balance

    def goto(self, dashboard_url: str):
        """導航到管理頁面。
        Vue 後台 SPA 有 websocket 長連線，不能用 networkidle。
        用 domcontentloaded + 等 tab button 出現判斷載入完成。
        """
        self.page.goto(
            f"{dashboard_url}#/management/all-management",
            wait_until="domcontentloaded",
        )
        # 等主內容區 tab 出現（代表 SPA hydration 完成）
        self.member_tab.wait_for(state="attached", timeout=15000)

    # -----------------------------------------------
    # 代理樹操作
    # -----------------------------------------------
    def click_agent_in_tree(self, agent_name: str):
        """
        在左側代理樹中找到並點擊指定代理。
        代理節點在 overflow 滾動容器中（DOM 存在但 hidden），
        使用 JS element.click() 直接觸發。
        """
        sh = get_screenshotter(self.page)

        agent_node = self.page.locator(
            f'span:text-is("{agent_name}")'
        ).first

        # 等待元素存在於 DOM（不要求 visible，因為可能在滾動區域外）
        agent_node.wait_for(state="attached", timeout=10000)

        if sh:
            sh.full_page(f"click_代理_{agent_name}_before")

        # 使用 JS click — dispatch_event 可能不觸發 Vue router
        self.page.evaluate(
            '(el) => el.click()',
            agent_node.element_handle()
        )

        # 等待列表重新渲染（不用 networkidle，SPA 有長連線）
        self._wait_for_list_loaded()

        if sh:
            sh.full_page(f"click_代理_{agent_name}_after")

    # -----------------------------------------------
    # Tab 切換
    # -----------------------------------------------
    def switch_to_member_tab(self):
        """切換到主內容區的會員 Tab"""
        sh = get_screenshotter(self.page)

        self.member_tab.wait_for(state="attached", timeout=5000)

        if sh:
            sh.full_page("click_會員Tab_before")

        # 使用 JS click 確保 Vue event handler 觸發
        self.page.evaluate(
            '(el) => el.click()',
            self.member_tab.element_handle()
        )

        self._wait_for_list_loaded()

        if sh:
            sh.full_page("click_會員Tab_after")

    def switch_to_agent_tab(self):
        """切換到主內容區的代理 Tab"""
        sh = get_screenshotter(self.page)

        self.agent_tab.wait_for(state="attached", timeout=5000)

        self.page.evaluate(
            '(el) => el.click()',
            self.agent_tab.element_handle()
        )

        self._wait_for_list_loaded()

    # -----------------------------------------------
    # 會員操作
    # -----------------------------------------------
    def _find_member_row(self, member_account: str) -> Locator:
        """
        找到包含指定會員帳號的列表行容器。
        會員列表可能在 overflow 容器中，元素存在但 hidden。
        先用 JS scrollIntoView 使其可見，再往上找包含操作按鈕的父層。
        """
        member_text = self.page.locator(
            f'span:text-is("{member_account}")'
        ).first

        # 等待 DOM 存在（不要求 visible — overflow 容器問題）
        member_text.wait_for(state="attached", timeout=10000)

        # 用 JS 滾動到元素位置
        self.page.evaluate(
            '(el) => el.scrollIntoView({block: "center"})',
            member_text.element_handle()
        )
        self.page.wait_for_timeout(500)

        # 往上找包含「存入」按鈕的最近容器（card/row）
        member_row = member_text.locator(
            'xpath=ancestor::*[.//button[contains(text(),"存入")]][1]'
        )

        member_row.wait_for(state="attached", timeout=5000)
        return member_row

    def get_member_balance(self, member_account: str) -> float:
        """
        讀取指定會員的當前餘額。
        從會員列表行文字中，找到「額度」標籤後的數字。
        餘額可能帶千分位逗號（如 "4,631.54"），解析為 float。
        """
        sh = get_screenshotter(self.page)

        member_row = self._find_member_row(member_account)

        # 從 member row 的全部文字中找「額度」標籤後的數字
        all_text = member_row.inner_text(timeout=5000)
        lines = [line.strip() for line in all_text.split('\n') if line.strip()]

        if sh:
            sh.full_page(f"verify_餘額_{member_account}")

        # 找到「額度」標籤後的第一個數字
        balance = None
        for i, line in enumerate(lines):
            if line == '額度':
                # 從下一行開始找數字
                for j in range(i + 1, min(i + 3, len(lines))):
                    if re.match(r'^[\d,]+\.?\d*$', lines[j]):
                        balance = float(lines[j].replace(',', ''))
                        break
                if balance is not None:
                    break

        if balance is None:
            # fallback：找不到「額度」標籤，嘗試用「存入」前的數字
            for i, line in enumerate(lines):
                if line == '存入':
                    # 往前找最近的數字
                    for j in range(i - 1, max(i - 3, -1), -1):
                        if re.match(r'^[\d,]+\.?\d*$', lines[j]):
                            balance = float(lines[j].replace(',', ''))
                            break
                    break

        if balance is None:
            raise ValueError(
                f"無法在會員 {member_account} 的列中找到餘額數值。"
                f"行文字摘要：{lines[:10]}"
            )

        return balance

    def deposit(self, member_account: str, amount: int, operator_password: Optional[str]):
        """
        對指定會員執行存入操作。
        流程：找到會員行 → 點存入按鈕 → 填金額 → 填操作者密碼 → 送出

        operator_password:
          - str（非空）：RC 後台 dialog 需填操作者密碼
          - None 或空字串：LT 後台 dialog 無此欄位，跳過密碼填寫
        """
        sh = get_screenshotter(self.page)

        member_row = self._find_member_row(member_account)

        # 點擊存入按鈕 — 使用 btn-primary（從 debug 觀察到的 class）
        deposit_btn = member_row.locator('button', has_text='存入').first
        deposit_btn.scroll_into_view_if_needed()
        if sh:
            sh.capture(deposit_btn, f"click_存入_{member_account}")

        self.page.evaluate('(el) => el.click()', deposit_btn.element_handle())

        # 處理存入彈窗
        self._fill_amount_dialog(amount, operator_password, "存入")

        if sh:
            sh.full_page(f"verify_存入完成_{member_account}_{amount}")

    def withdraw(self, member_account: str, amount: int, operator_password: Optional[str]):
        """
        對指定會員執行提取操作。
        流程：找到會員行 → 點提取按鈕 → 填金額 → 填操作者密碼 → 送出

        operator_password:
          - str（非空）：RC 後台 dialog 需填操作者密碼
          - None 或空字串：LT 後台 dialog 無此欄位，跳過密碼填寫
        """
        sh = get_screenshotter(self.page)

        member_row = self._find_member_row(member_account)

        # 點擊提取按鈕
        withdraw_btn = member_row.locator('button', has_text='提取').first
        withdraw_btn.scroll_into_view_if_needed()
        if sh:
            sh.capture(withdraw_btn, f"click_提取_{member_account}")

        self.page.evaluate('(el) => el.click()', withdraw_btn.element_handle())

        # 處理提取彈窗
        self._fill_amount_dialog(amount, operator_password, "提取")

        if sh:
            sh.full_page(f"verify_提取完成_{member_account}_{amount}")

    # -----------------------------------------------
    # 總代 → 代理 派點（站長層級，2026-06-26 probe 確認）
    #
    # 總代登入後，代理 tab 每個下線代理為一張 `.tab-item` 卡片（與 RF dashboard 同結構）：
    #   存入 = button.btn-primary.me-2、提取 = button.btn-primary:not(.me-2)。
    # 金額 dialog 與會員存提相同 → 複用 _fill_amount_dialog。
    # 信用版總代剩餘額度為 ∞ → 測試只驗「目標代理」餘額變化（不驗總代側）。
    # 目標代理餘額讀法：開存提 dialog，dialog 內顯示「上級代理…剩餘額度 ∞ / 代理帳號…剩餘額度 N」，
    #   取最後一個數值型「剩餘額度」即目標代理餘額（實時值）。
    # -----------------------------------------------

    def set_agent_page_size(self, size: int = 500):
        """把代理列表每頁筆數開到最大，確保目標代理（可能在後面頁）進 DOM。

        代理 tab 預設 50/頁；代理數可能上百（如 LT 166）→ 目標代理常不在第 1 頁。
        頁面有多個 select（頁碼用 1/2…、每頁筆數用 10/20/50/100/200/500），
        找含目標 size 選項的那個 select 設定即可。
        """
        self.page.evaluate(
            """(size) => {
                for (const s of document.querySelectorAll('select')) {
                    const opts = [...s.options].map(o => o.value);
                    if (opts.includes(String(size))) {
                        s.value = String(size);
                        s.dispatchEvent(new Event('change', { bubbles: true }));
                        return;
                    }
                }
            }""",
            size,
        )
        self._wait_for_list_loaded()

    def _agent_card(self, agent_account: str) -> Locator:
        """精準鎖定代理卡片：含「文字恰為帳號」元素的 .tab-item（唯一）。
        用 tag-agnostic 的 :text-is（不綁 span）：RE/LT 代理名可能渲染為 <a> 而非 <span>。
        呼叫前建議先 set_agent_page_size() 把全部代理載入 DOM（目標可能在後面頁）。
        """
        card = self.page.locator(".tab-item").filter(
            has=self.page.locator(f':text-is("{agent_account}")')
        )
        card.first.wait_for(state="attached", timeout=15000)
        return card.first

    def _read_dialog_target_balance(self) -> float:
        """讀存提 dialog 內目標代理的剩餘額度（最後一個數值型『剩餘額度 N』）。"""
        text = self.page.evaluate(
            """() => {
                const sub = [...document.querySelectorAll('button.primary-button')]
                    .find(b => /送出/.test(b.textContent));
                if (!sub) return null;
                let dlg = sub;
                while (dlg && !(dlg.className||'').includes('dialog-container')) dlg = dlg.parentElement;
                if (!dlg) return null;
                const m = dlg.innerText.match(/剩餘額度\\s*([\\d,]+)/g);
                if (!m || !m.length) return null;
                return m[m.length-1].replace(/[^\\d,]/g, '');
            }"""
        )
        if text is None:
            raise ValueError("無法從存提 dialog 讀取目標代理剩餘額度")
        return float(text.replace(",", ""))

    def _cancel_dialog(self):
        """點 dialog 取消鈕關閉（讀餘額用，不送出）。"""
        self.page.evaluate(
            """() => {
                const c = [...document.querySelectorAll('button.secondary-button, button')]
                    .find(b => /取消/.test(b.textContent));
                if (c) c.click();
            }"""
        )
        self.page.wait_for_timeout(500)

    def get_agent_balance(self, agent_account: str) -> float:
        """開存入 dialog 讀目標代理當前剩餘額度 → 取消關閉（不動餘額）。"""
        sh = get_screenshotter(self.page)
        card = self._agent_card(agent_account)
        dep_btn = card.locator("button.btn-primary.me-2").first
        dep_btn.wait_for(state="attached", timeout=5000)
        self.page.evaluate("(el) => el.click()", dep_btn.element_handle())
        # 等 dialog 顯示數值型「剩餘額度 N」後再讀，取代硬等 800ms
        dialog = self.page.locator(".dialog-container").last
        wait_for_text_matches(dialog, re.compile(r"剩餘額度\s*[\d,]+"), timeout=8000)
        balance = self._read_dialog_target_balance()
        if sh:
            sh.full_page(f"verify_代理餘額_{agent_account}_{balance}")
        self._cancel_dialog()
        return balance

    def deposit_to_agent(self, agent_account: str, amount: int, operator_password: Optional[str] = None):
        """總代對指定下線代理存入（派點）。複用會員存提 dialog。

        operator_password：RD 站 dialog 有操作者密碼欄（總代層級＝總代密碼）；
        RC/RE/LT 無此欄，_fill_amount_dialog 偵測不到 password input 會自動略過，
        故 caller 統一傳 site_config.dashboard_pass 即可跨站相容。
        """
        sh = get_screenshotter(self.page)
        card = self._agent_card(agent_account)
        dep_btn = card.locator("button.btn-primary.me-2").first
        dep_btn.wait_for(state="attached", timeout=5000)
        if sh:
            sh.capture(dep_btn, f"click_代理存入_{agent_account}_{amount}")
        self.page.evaluate("(el) => el.click()", dep_btn.element_handle())
        self._fill_amount_dialog(amount, operator_password, "存入")
        if sh:
            sh.full_page(f"verify_代理存入完成_{agent_account}_{amount}")

    def withdraw_from_agent(self, agent_account: str, amount: int, operator_password: Optional[str] = None):
        """總代對指定下線代理提取（收點）。複用會員存提 dialog。
        operator_password 同 deposit_to_agent 說明。
        """
        sh = get_screenshotter(self.page)
        card = self._agent_card(agent_account)
        wd_btn = card.locator("button.btn-primary:not(.me-2)").first
        wd_btn.wait_for(state="attached", timeout=5000)
        if sh:
            sh.capture(wd_btn, f"click_代理提取_{agent_account}_{amount}")
        self.page.evaluate("(el) => el.click()", wd_btn.element_handle())
        self._fill_amount_dialog(amount, operator_password, "提取")
        if sh:
            sh.full_page(f"verify_代理提取完成_{agent_account}_{amount}")

    # -----------------------------------------------
    # 內部 helpers
    # -----------------------------------------------
    def _fill_amount_dialog(
        self,
        amount: int,
        operator_password: Optional[str],
        operation: str,
    ):
        """
        填寫存入/提取彈窗：金額 + (可選)操作者密碼 + 點送出。

        operator_password:
          - 非空字串：dialog 內有 input[type=password] 時填入；無則略過
            （RC 後台 2026-05-29 改版：操作者密碼欄位移除，dialog 只剩金額；
             LT 後台一直無密碼欄。caller 仍可保留傳值以維持簽名）
          - None 或空字串：直接跳過

        定位策略：
          頁面可能同時有多個 .dialog-container（常駐容器 + 彈出的 dialog），
          用剛開啟的 dialog 專屬的「送出」按鈕作為 anchor，
          反推其 ancestor `.dialog-container` 作為 input 搜尋範圍，
          避免誤抓頁面其他位置的 input。
        """
        sh = get_screenshotter(self.page)

        # 等「送出」按鈕出現（代表存入/提取 dialog 已開啟）
        submit_btn = self.page.locator('button.primary-button', has_text='送出').first
        submit_btn.wait_for(state="visible", timeout=5000)

        # 從送出按鈕反推所在的 dialog 容器，scope 後續 input 搜尋
        dialog = submit_btn.locator('xpath=ancestor::*[contains(@class,"dialog-container")][1]')

        if sh:
            sh.full_page(f"dialog_{operation}_opened")

        # 填入金額 — dialog 範圍內的 text input（排除 multiselect searchbox）
        amount_input = dialog.locator(
            'input[type="text"]:not(.multiselect__input)'
        ).first
        amount_input.wait_for(state="visible", timeout=3000)

        if sh:
            sh.capture(amount_input, f"fill_{operation}_金額_{amount}")
        amount_input.fill(str(amount))

        # 填入操作者密碼（若 dialog 內有 password input；現行 RC/LT 都無，保留以兼容未來）
        if operator_password:
            password_input = dialog.locator('input[type="password"]').first
            if password_input.count() > 0:
                password_input.wait_for(state="visible", timeout=3000)
                if sh:
                    sh.capture(password_input, f"fill_{operation}_操作者密碼")
                password_input.fill(operator_password)

        # 點擊送出
        if sh:
            sh.capture(submit_btn, f"click_{operation}_送出")
        submit_btn.click()

        # 等待彈窗關閉（送出按鈕消失）+ 列表更新
        try:
            submit_btn.wait_for(state="hidden", timeout=10000)
        except PlaywrightTimeoutError:
            try:
                ok_btn = self.page.locator('button', has_text='確定')
                ok_btn.click(timeout=2000)
            except PlaywrightTimeoutError:
                pass
        self._wait_for_list_loaded()

    def _wait_for_list_loaded(self):
        """等待列表載入完成"""
        try:
            loading = self.page.locator('.el-loading-mask, .loading, [class*="loading"]')
            loading.wait_for(state="hidden", timeout=5000)
        except PlaywrightTimeoutError:
            pass
        # 額外等待 DOM 穩定
        self.page.wait_for_timeout(1000)
