"""
LT 後台會員充值測試（存入/提取）
LT-DASH-001

使用 .env 的 SITE_LT_DASHBOARD_AGENT_USER（自動化代理帳號）登入後台，
對其底下會員 SITE_LT_USERNAME 進行存入與提取操作，
驗證會員餘額與代理剩餘額度正確增減。

Rollback 設計（精簡版）：存入/提取使用對稱金額，normal path 結束時餘額與
代理額度皆回到初始值。若中途失敗（存入後但提取前），finally 以補償提取復原。

未來優化方向：
- A. Fixture 化：把 rollback 抽到 pytest fixture (yield) 的 teardown，多個
     dashboard 測試可共用，不用每個 test body 寫 try/finally。
- B. 通用安全網：teardown 時直接 diff 餘額（current vs initial），非 0 就反向
     補償，不依賴 deposit_done flag；能涵蓋任意中間狀態的偏移。
- C. API / DB 層 transaction rollback：跳過 UI，透過後端 snapshot 還原；最
     乾淨但需要 backend 端點支援。
"""

import pytest
from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError
from pages.dashboard.factory import get_dashboard_management_page_class


# 測試資料（帳號從 .env 讀取）
AMOUNT = 10


@pytest.mark.p1
@pytest.mark.lt
@pytest.mark.dashboard
@pytest.mark.wallet
class TestMemberTopUp:
    """LT-DASH-001：後台會員存入/提取餘額驗證"""

    def test_deposit_and_withdraw(self, dashboard_page: Page, site_config):
        """LT-DASH-001：存入 10 → 驗證 +10 → 提取 10 → 驗證回到初始（含 finally rollback）"""
        ManagementPage = get_dashboard_management_page_class(site_config.site_id)
        mgmt = ManagementPage(dashboard_page)
        agent_name = site_config.dashboard_agent_user
        member_account = site_config.username

        # 1. 點擊側邊欄代理樹中的代理，再切到會員 Tab
        mgmt.click_agent_in_tree(agent_name)
        mgmt.switch_to_member_tab()

        # 2. 記錄存入前：會員餘額 + 代理剩餘額度
        balance_before = mgmt.get_member_balance(member_account)
        agent_balance_before = mgmt.get_agent_remaining_balance()

        deposit_done = False
        try:
            # 3. 存入 10（LT 後台 dialog 無操作者密碼欄位）
            mgmt.deposit(member_account, AMOUNT, operator_password=None)
            deposit_done = True

            # 4. 驗證會員餘額增加
            balance_after_deposit = mgmt.get_member_balance(member_account)
            assert balance_after_deposit == pytest.approx(balance_before + AMOUNT, abs=0.01), (
                f"存入 {AMOUNT} 後會員餘額應為 {balance_before + AMOUNT}，"
                f"實際為 {balance_after_deposit}"
            )

            # 5. 驗證代理剩餘額度減少（存入給會員 = 代理額度轉出）
            agent_balance_after_deposit = mgmt.get_agent_remaining_balance()
            assert agent_balance_after_deposit == pytest.approx(agent_balance_before - AMOUNT, abs=0.01), (
                f"存入 {AMOUNT} 後代理剩餘額度應為 {agent_balance_before - AMOUNT}，"
                f"實際為 {agent_balance_after_deposit}"
            )

            # 6. 提取 10（對稱金額，將餘額與代理額度復原）
            mgmt.withdraw(member_account, AMOUNT, operator_password=None)
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
                    mgmt.withdraw(member_account, AMOUNT, operator_password=None)
                except PlaywrightTimeoutError:
                    pass  # best-effort，不遮蔽原始錯誤
