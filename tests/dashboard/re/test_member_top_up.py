"""
RE 後台會員充值測試 (BeWin) — 存入/提取
RE-DASH-001

使用 .env 的 SITE_RE_DASHBOARD_AGENT_USER（<RE 代理帳號>，自動化代理）登入後台，
對其底下會員 SITE_RE_USERNAME（<RE 會員帳號>）進行存入與提取操作，
驗證會員餘額與代理剩餘額度正確增減。

對齊 tests/dashboard/rc/test_member_top_up.py 的設計（rollback 補償、對稱金額）。
"""

import pytest
from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError
from pages.dashboard.factory import get_dashboard_management_page_class


# 測試資料（代理帳號=SITE_RE_DASHBOARD_AGENT_USER、會員帳號=SITE_RE_USERNAME）
AMOUNT = 10  # 存入/提取對稱金額，測試結束餘額應回到初始值


@pytest.mark.p1
@pytest.mark.re
@pytest.mark.dashboard
@pytest.mark.wallet
class TestMemberTopUp:
    """RE-DASH-001：後台會員存入/提取餘額驗證"""

    def test_deposit_and_withdraw(self, dashboard_page: Page, site_config):
        """RE-DASH-001：存入 10 → 驗證 +10 → 提取 10 → 驗證回到初始（含 finally rollback）"""
        ManagementPage = get_dashboard_management_page_class(site_config.site_id)
        mgmt = ManagementPage(dashboard_page)
        member_account = site_config.username
        operator_password = site_config.dashboard_agent_pass

        # 1. 切到會員 Tab（自動化代理登入後直接在自己的管理頁，不需導航代理樹）
        mgmt.switch_to_member_tab()

        # 2. 記錄存入前：會員餘額 + 代理剩餘額度
        balance_before = mgmt.get_member_balance(member_account)
        agent_balance_before = mgmt.get_agent_remaining_balance()

        deposit_done = False
        try:
            # 3. 存入 10（操作者密碼 = 代理帳號密碼）
            mgmt.deposit(member_account, AMOUNT, operator_password=operator_password)
            deposit_done = True

            # 4. 驗證會員餘額增加
            balance_after_deposit = mgmt.get_member_balance(member_account)
            assert balance_after_deposit == pytest.approx(balance_before + AMOUNT, abs=0.01), (
                f"存入 {AMOUNT} 後會員餘額應為 {balance_before + AMOUNT}，"
                f"實際為 {balance_after_deposit}"
            )

            # 5. 驗證代理剩餘額度減少
            agent_balance_after_deposit = mgmt.get_agent_remaining_balance()
            assert agent_balance_after_deposit == pytest.approx(agent_balance_before - AMOUNT, abs=0.01), (
                f"存入 {AMOUNT} 後代理剩餘額度應為 {agent_balance_before - AMOUNT}，"
                f"實際為 {agent_balance_after_deposit}"
            )

            # 6. 提取 10（對稱金額，將餘額與代理額度復原）
            mgmt.withdraw(member_account, AMOUNT, operator_password=operator_password)
            deposit_done = False  # withdraw 已抵銷 deposit，無需 finally rollback

            # 7. 驗證會員餘額回到初始
            balance_after_withdraw = mgmt.get_member_balance(member_account)
            assert balance_after_withdraw == pytest.approx(balance_before, abs=0.01), (
                f"提取 {AMOUNT} 後會員餘額應回到初始 {balance_before}，"
                f"實際為 {balance_after_withdraw}"
            )

            # 8. 驗證代理剩餘額度回到初始
            agent_balance_after_withdraw = mgmt.get_agent_remaining_balance()
            assert agent_balance_after_withdraw == pytest.approx(agent_balance_before, abs=0.01), (
                f"提取 {AMOUNT} 後代理剩餘額度應回到初始 {agent_balance_before}，"
                f"實際為 {agent_balance_after_withdraw}"
            )
        finally:
            # Rollback: deposit 完成但 withdraw 未完成（assertion 失敗或中途拋例外）時補償
            if deposit_done:
                try:
                    mgmt.withdraw(member_account, AMOUNT, operator_password=operator_password)
                except PlaywrightTimeoutError:
                    pass  # best-effort，不遮蔽原始錯誤
