"""
後台管理頁面 Page Object — RE 站點 (BeWin)
處理：Tab 切換（代理/會員/子帳號）、代理樹導航、會員存入/提取操作

與 RC 共用 t9platform 後台 DOM。差異：
- RE 的會員/代理名稱可能渲染為 `<a>` 連結（RC 是 `<span>`）；
  `_find_member_row` 使用 `text="..."` 不限定 tag，相容兩種。
- 主內容區 tab 不能用 `evaluate('el => el.click()')` 觸發（事件不冒泡），
  改用 Playwright 直接 `click()`，與 RE 後台實機行為一致。

代理樹節點在 overflow 滾動容器中，DOM 存在但可能 hidden，
需使用 JS click 或 dispatch_event 點擊。
"""

import re
from typing import Optional
from playwright.sync_api import Page, Locator, expect, TimeoutError as PlaywrightTimeoutError
from utils.screenshot_helper import get_screenshotter
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

        value_el = title.locator('xpath=following-sibling::p[contains(@class,"info-value")]').first
        value_text = value_el.inner_text(timeout=3000)

        balance = float(value_text.strip().replace(',', ''))

        if sh:
            sh.full_page(f"verify_代理剩餘額度_{balance}")

        return balance

    def goto(self, dashboard_url: str):
        """導航到管理頁面。
        Vue 後台 SPA 有 websocket 長連線，不能用 networkidle。
        """
        self.page.goto(
            f"{dashboard_url}#/management/all-management",
            wait_until="domcontentloaded",
        )
        self.member_tab.wait_for(state="attached", timeout=15000)

    # -----------------------------------------------
    # 代理樹操作
    # -----------------------------------------------
    def click_agent_in_tree(self, agent_name: str):
        """在左側代理樹中找到並點擊指定代理。"""
        sh = get_screenshotter(self.page)

        agent_node = self.page.get_by_text(agent_name, exact=True).first
        agent_node.wait_for(state="attached", timeout=10000)

        if sh:
            sh.full_page(f"click_代理_{agent_name}_before")

        self.page.evaluate(
            '(el) => el.click()',
            agent_node.element_handle()
        )
        self._wait_for_list_loaded()

        if sh:
            sh.full_page(f"click_代理_{agent_name}_after")

    # -----------------------------------------------
    # Tab 切換
    # -----------------------------------------------
    def switch_to_member_tab(self):
        """切換到主內容區的會員 Tab。

        實機 probe 確認 RE 站用 evaluate('el => el.click()') 不會觸發 Vue handler，
        必須用 Playwright `click()`（會走 hit testing + dispatch native events）。
        """
        sh = get_screenshotter(self.page)

        self.member_tab.wait_for(state="visible", timeout=5000)

        if sh:
            sh.full_page("click_會員Tab_before")

        self.member_tab.first.click()
        self._wait_for_list_loaded()

        if sh:
            sh.full_page("click_會員Tab_after")

    def switch_to_agent_tab(self):
        """切換到主內容區的代理 Tab"""
        sh = get_screenshotter(self.page)

        self.agent_tab.wait_for(state="visible", timeout=5000)
        self.agent_tab.first.click()
        self._wait_for_list_loaded()

    # -----------------------------------------------
    # 會員操作
    # -----------------------------------------------
    def _find_member_row(self, member_account: str) -> Locator:
        """
        找到包含指定會員帳號的列表行容器。
        RE 會員名稱渲染為 `<a>` 連結，不能用 `span:text-is(...)`，
        改用 `get_by_text(exact=True)` 不限定 tag。
        """
        member_text = self.page.get_by_text(member_account, exact=True).first

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
        """
        sh = get_screenshotter(self.page)

        member_row = self._find_member_row(member_account)

        all_text = member_row.inner_text(timeout=5000)
        lines = [line.strip() for line in all_text.split('\n') if line.strip()]

        if sh:
            sh.full_page(f"verify_餘額_{member_account}")

        balance = None
        for i, line in enumerate(lines):
            if line == '額度':
                for j in range(i + 1, min(i + 3, len(lines))):
                    if re.match(r'^[\d,]+\.?\d*$', lines[j]):
                        balance = float(lines[j].replace(',', ''))
                        break
                if balance is not None:
                    break

        if balance is None:
            for i, line in enumerate(lines):
                if line == '存入':
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
        """對指定會員執行存入操作。"""
        sh = get_screenshotter(self.page)

        member_row = self._find_member_row(member_account)

        deposit_btn = member_row.locator('button', has_text='存入').first
        deposit_btn.scroll_into_view_if_needed()
        if sh:
            sh.capture(deposit_btn, f"click_存入_{member_account}")

        self.page.evaluate('(el) => el.click()', deposit_btn.element_handle())

        self._fill_amount_dialog(amount, operator_password, "存入")

        if sh:
            sh.full_page(f"verify_存入完成_{member_account}_{amount}")

    def withdraw(self, member_account: str, amount: int, operator_password: Optional[str]):
        """對指定會員執行提取操作。"""
        sh = get_screenshotter(self.page)

        member_row = self._find_member_row(member_account)

        withdraw_btn = member_row.locator('button', has_text='提取').first
        withdraw_btn.scroll_into_view_if_needed()
        if sh:
            sh.capture(withdraw_btn, f"click_提取_{member_account}")

        self.page.evaluate('(el) => el.click()', withdraw_btn.element_handle())

        self._fill_amount_dialog(amount, operator_password, "提取")

        if sh:
            sh.full_page(f"verify_提取完成_{member_account}_{amount}")

    # -----------------------------------------------
    # 總代 → 代理 派點（站長層級，2026-06-26）
    # RE 自有 POM（非 re-export RC），故同套方法在此複製一份。
    # 代理 tab 每個下線代理為 .tab-item 卡片：存入 button.btn-primary.me-2、提取 :not(.me-2)。
    # 金額 dialog 與會員存提相同 → 複用 _fill_amount_dialog。總代額度 ∞ → 只驗代理側餘額。
    # -----------------------------------------------

    def set_agent_page_size(self, size: int = 500):
        """把代理列表每頁筆數開到最大，確保目標代理（可能在後面頁）進 DOM。
        找含目標 size 選項（10/20/50/100/200/500）的 select 設定。"""
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
        """精準鎖定代理卡片：含「文字恰為帳號」元素的 .tab-item（tag-agnostic，相容 <a>/<span>）。
        呼叫前建議先 set_agent_page_size() 把全部代理載入 DOM（目標可能在後面頁）。"""
        card = self.page.locator(".tab-item").filter(
            has=self.page.locator(f':text-is("{agent_account}")')
        )
        card.first.wait_for(state="attached", timeout=15000)
        return card.first

    def _read_dialog_target_balance(self) -> float:
        """讀存提 dialog 內目標代理剩餘額度（最後一個數值型『剩餘額度 N』）。"""
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
        """總代對指定下線代理存入（派點）。複用會員存提 dialog。"""
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
        """總代對指定下線代理提取（收點）。複用會員存提 dialog。"""
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
        """填寫存入/提取彈窗：金額 + (可選)操作者密碼 + 點送出。"""
        sh = get_screenshotter(self.page)

        submit_btn = self.page.locator('button.primary-button', has_text='送出').first
        submit_btn.wait_for(state="visible", timeout=5000)

        dialog = submit_btn.locator('xpath=ancestor::*[contains(@class,"dialog-container")][1]')

        if sh:
            sh.full_page(f"dialog_{operation}_opened")

        amount_input = dialog.locator(
            'input[type="text"]:not(.multiselect__input)'
        ).first
        amount_input.wait_for(state="visible", timeout=3000)

        if sh:
            sh.capture(amount_input, f"fill_{operation}_金額_{amount}")
        amount_input.fill(str(amount))

        if operator_password:
            password_input = dialog.locator('input[type="password"]').first
            password_input.wait_for(state="visible", timeout=3000)
            if sh:
                sh.capture(password_input, f"fill_{operation}_操作者密碼")
            password_input.fill(operator_password)

        if sh:
            sh.capture(submit_btn, f"click_{operation}_送出")
        submit_btn.click()

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
        self.page.wait_for_timeout(1000)
