"""
LT 後台會員充值測試（存入/提取）
LT-DASH-001

使用自動化代理帳號 qadlttest1 登入後台，
對其底下會員 dltauto02 進行存入與提取操作，
驗證會員餘額與代理剩餘額度正確增減。
"""

import pytest
from playwright.sync_api import Page
from pages.dashboard.factory import get_dashboard_management_page_class
from utils.screenshot_helper import get_screenshotter


# 測試資料
AGENT_NAME = "qadlttest1"
MEMBER_ACCOUNT = "dltauto02"
DEPOSIT_AMOUNT = 10
WITHDRAW_AMOUNT = 5


@pytest.mark.p1
@pytest.mark.lt
@pytest.mark.dashboard
@pytest.mark.wallet
class TestMemberTopUp:
    """LT-DASH-001：後台會員存入/提取餘額驗證"""

    def test_deposit_and_withdraw(self, dashboard_page: Page, site_config):
        """LT-DASH-001：存入 10 → 驗證餘額 +10 → 提取 5 → 驗證餘額 -5（含代理剩餘額度檢查）"""
        ManagementPage = get_dashboard_management_page_class(site_config.site_id)
        mgmt = ManagementPage(dashboard_page)

        # 1. 點擊側邊欄代理樹中的 qadlttest1，再切到會員 Tab
        mgmt.click_agent_in_tree(AGENT_NAME)
        mgmt.switch_to_member_tab()

        # 2. 記錄存入前：會員餘額 + 代理剩餘額度
        balance_before = mgmt.get_member_balance(MEMBER_ACCOUNT)
        agent_balance_before = mgmt.get_agent_remaining_balance()

        # 3. 存入 10（操作者密碼 = 代理帳號密碼）
        mgmt.deposit(
            MEMBER_ACCOUNT,
            DEPOSIT_AMOUNT,
            operator_password=""
        )

        # 4. 驗證會員餘額增加
        balance_after_deposit = mgmt.get_member_balance(MEMBER_ACCOUNT)
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
            MEMBER_ACCOUNT,
            WITHDRAW_AMOUNT,
            operator_password=""
        )

        # 7. 驗證會員餘額減少
        balance_after_withdraw = mgmt.get_member_balance(MEMBER_ACCOUNT)
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
