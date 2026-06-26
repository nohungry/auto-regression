"""
LT 後台 — 總代（站長層級）對下線代理派點測試（存入/提取）
LT-DASH-MASTER-TOPUP-001

信用版三層額度模型：總代 → 代理 → 會員，上層派點 = 上層扣、下層加。
既有 test_member_top_up 測「代理→會員」這層；本檔補測**最上層「總代→代理」**。

⚠️ 帳號層級：**總代帳號**（SITE_LT_DASHBOARD_USER，無 2FA）。
   登入後代理 tab 每個下線代理為一張 .tab-item 卡片（probe 2026-06-26 確認，與 RF dashboard 同結構）。

範圍說明（信用版總代剩餘額度為 ∞）：
- 總代額度無限 → 派點後總代仍為 ∞，無法做「總代 -N」斷言。
- 故本測試**只驗目標代理側餘額變化**（存入 +N → 提取還原），不驗總代側。
- 仍完整覆蓋「總代能派點給代理 + 代理餘額正確增減 + 可逆」。

對稱可逆 + finally diff 補償：存入 N → 驗代理 +N → 提取 N 還原 → 驗回初始；
中途失敗時 finally 依差額補回，確保 qadrctest 餘額不留殘差、可重跑。

目標代理用 site_config.dashboard_agent_user（= lt 代理，總代直屬下線、與 member 測試同帳號）。
"""

import pytest
from playwright.sync_api import Page

from pages.dashboard.factory import get_dashboard_management_page_class

AMOUNT = 1  # 派點/收點對稱金額，測試結束額度應回到初始；小額避免影響業務


@pytest.mark.p1
@pytest.mark.lt
@pytest.mark.dashboard
@pytest.mark.wallet
class TestMasterToAgentTopUp:
    """LT-DASH-MASTER-TOPUP-001：總代對代理存入/提取額度驗證（只驗代理側，總代 ∞）。"""

    def test_master_deposit_withdraw_to_agent(self, master_dashboard_page: Page, site_config):
        Mgmt = get_dashboard_management_page_class(site_config.site_id)
        mgmt = Mgmt(master_dashboard_page)
        agent = site_config.dashboard_agent_user  # qadrctest，不寫死帳號

        mgmt.goto(site_config.dashboard_url)
        mgmt.switch_to_agent_tab()
        mgmt.set_agent_page_size()  # 代理數可能上百，開大每頁確保目標代理在 DOM
        before = mgmt.get_agent_balance(agent)
        print(f"\n[master-topup] {agent} before balance={before}")

        try:
            # --- 存入（總代派點給代理）N ---
            mgmt.deposit_to_agent(agent, AMOUNT, operator_password=site_config.dashboard_pass)
            after_dep = mgmt.get_agent_balance(agent)
            print(f"[master-topup] after deposit={after_dep}")
            assert after_dep == pytest.approx(before + AMOUNT, abs=0.01), (
                f"總代存入 {AMOUNT} 後 {agent} 餘額應為 {before + AMOUNT}，實得 {after_dep}"
            )

            # --- 提取（總代收回）N，還原 ---
            mgmt.withdraw_from_agent(agent, AMOUNT, operator_password=site_config.dashboard_pass)
            after_wd = mgmt.get_agent_balance(agent)
            print(f"[master-topup] after withdraw={after_wd}")
            assert after_wd == pytest.approx(before, abs=0.01), (
                f"總代提取 {AMOUNT} 後 {agent} 餘額應回到初始 {before}，實得 {after_wd}"
            )
        finally:
            # 保險補償：把代理餘額拉回 before（diff=0 則 no-op）。best-effort，不遮蔽原始失敗。
            try:
                cur = mgmt.get_agent_balance(agent)
                diff = round(cur - before)
                if diff > 0:
                    mgmt.withdraw_from_agent(agent, abs(diff), operator_password=site_config.dashboard_pass)
                    print(f"[rollback] 提取補償 {abs(diff)} → 還原至 {before}")
                elif diff < 0:
                    mgmt.deposit_to_agent(agent, abs(diff), operator_password=site_config.dashboard_pass)
                    print(f"[rollback] 存入補償 {abs(diff)} → 還原至 {before}")
            except Exception as e:  # noqa: BLE001 — 補償 best-effort，僅警告
                print(f"[rollback warning] 補償未完成：{type(e).__name__}: {e}")
