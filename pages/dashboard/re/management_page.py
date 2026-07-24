"""
後台管理頁面 Page Object — RE 站點 (BeWin)

RE 後台與 RC 共用信用版後台 DOM 結構（同平台），本檔繼承
`pages.dashboard.rc.management_page.ManagementPage`，只覆寫實機 probe
確認的兩類差異（其餘方法全數繼承 RC 實作）：

- **Vue tab 需 native click**：RE 主內容區 tab 用 `evaluate('el => el.click()')`
  不會觸發 Vue handler（事件不冒泡），必須用 Playwright `click()`（走 hit
  testing + dispatch native events）→ 覆寫 `switch_to_member_tab` /
  `switch_to_agent_tab`。
- **會員/代理名稱渲染為 `<a>` 連結**（RC 是 `<span>`），不能用
  `span:text-is(...)`，改用 `get_by_text(exact=True)` 不限定 tag →
  覆寫 `click_agent_in_tree` / `_find_member_row`。

沿革：原為 RC 的整檔複製（388 行）；2026-07-21 依 login_page.py 預告的
「未來若 RE 後台出現差異，可改為 subclass 覆寫」路線改寫為繼承。
"""

from playwright.sync_api import Locator

from pages.dashboard.rc.management_page import ManagementPage as _RCManagementPage
from utils.screenshot_helper import get_screenshotter


class ManagementPage(_RCManagementPage):

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
