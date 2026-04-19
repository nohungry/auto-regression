"""
RC 後台會員充值測試（存入/提取）
RC-DASH-001

使用 .env 的 SITE_RC_DASHBOARD_AGENT_USER 登入後台，
對其底下會員 SITE_RC_USERNAME 進行存入與提取操作，
驗證會員餘額與代理剩餘額度正確增減。
"""

import pytest
from playwright.sync_api import Page
from pages.dashboard.factory import get_dashboard_management_page_class


# 測試資料（會員帳號從 .env 的 SITE_RC_USERNAME 讀取）
DEPOSIT_AMOUNT = 10
WITHDRAW_AMOUNT = 5


@pytest.mark.p1
@pytest.mark.rc
@pytest.mark.dashboard
@pytest.mark.wallet
class TestMemberTopUp:
    """RC-DASH-001：後台會員存入/提取餘額驗證"""

    def test_deposit_and_withdraw(self, dashboard_page: Page, site_config):
        """RC-DASH-001：存入 10 → 驗證餘額 +10 → 提取 5 → 驗證餘額 -5（含代理剩餘額度檢查）"""
        ManagementPage = get_dashboard_management_page_class(site_config.site_id)
        mgmt = ManagementPage(dashboard_page)
        member_account = site_config.username

        # 1. 切到會員 Tab（自動化代理登入後直接在自己的管理頁，不需導航代理樹）
        mgmt.switch_to_member_tab()

        # 2. 記錄存入前：會員餘額 + 代理剩餘額度
        balance_before = mgmt.get_member_balance(member_account)
        agent_balance_before = mgmt.get_agent_remaining_balance()

        # 3. 存入 10（操作者密碼 = 代理帳號密碼）
        mgmt.deposit(
            member_account,
            DEPOSIT_AMOUNT,
            operator_password=site_config.dashboard_agent_pass,
        )

        # 4. 驗證會員餘額增加
        balance_after_deposit = mgmt.get_member_balance(member_account)
        assert balance_after_deposit == pytest.approx(balance_before + DEPOSIT_AMOUNT, abs=0.01), (
            f"存入 {DEPOSIT_AMOUNT} 後會員餘額應為 {balance_before + DEPOSIT_AMOUNT}，"
            f"實際為 {balance_after_deposit}"
        )

        # 5. 驗證代理剩餘額度減少（存入給會員 = 代理額度轉出）
        agent_balance_after_deposit = mgmt.get_agent_remaining_balance()
        assert agent_balance_after_deposit == pytest.approx(agent_balance_before - DEPOSIT_AMOUNT, abs=0.01), (
            f"存入 {DEPOSIT_AMOUNT} 後代理剩餘額度應為 {agent_balance_before - DEPOSIT_AMOUNT}，"
            f"實際為 {agent_balance_after_deposit}"
        )

        # 6. 提取 5（直接操作，不需重新找會員）
        mgmt.withdraw(
            member_account,
            WITHDRAW_AMOUNT,
            operator_password=site_config.dashboard_agent_pass,
        )

        # 7. 驗證會員餘額減少
        balance_after_withdraw = mgmt.get_member_balance(member_account)
        assert balance_after_withdraw == pytest.approx(balance_after_deposit - WITHDRAW_AMOUNT, abs=0.01), (
            f"提取 {WITHDRAW_AMOUNT} 後會員餘額應為 {balance_after_deposit - WITHDRAW_AMOUNT}，"
            f"實際為 {balance_after_withdraw}"
        )

        # 8. 驗證代理剩餘額度增加（從會員提取 = 代理額度回收）
        agent_balance_after_withdraw = mgmt.get_agent_remaining_balance()
        assert agent_balance_after_withdraw == pytest.approx(agent_balance_after_deposit + WITHDRAW_AMOUNT, abs=0.01), (
            f"提取 {WITHDRAW_AMOUNT} 後代理剩餘額度應為 {agent_balance_after_deposit + WITHDRAW_AMOUNT}，"
            f"實際為 {agent_balance_after_withdraw}"
        )
