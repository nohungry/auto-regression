"""
RF 後台 — 總代（站長層級）對下線代理派點測試（存入/提取）
RF-DASH-MASTER-TOPUP-001

信用版三層額度模型 總代→代理→會員。RF 既有 test_dashboard_topup 測「站長→會員」；
本檔補測**「總代→代理」**，補齊信用版 5 站（RC/RE/LT/RD #118 + RF 本檔）最上層覆蓋。

⚠️ 帳號層級：**站長/總代帳號**（SITE_RF_DASHBOARD_USER，無 2FA）。
   RF 站長即總代層級（probe 2026-06-27：代理 tab 列 8 個下線代理，目標代理 qaautodrf 可定位）。

範圍（信用版總代餘額 = ∞）：
- 總代額度無限 → 派點後總代仍 ∞，無法做「總代 -N」斷言 → **只驗目標代理側餘額變化**（同 #118）。
- dialog 餘額：label-xs[1]=代理餘額（[0]=上級總代 ∞）。

對稱可逆 + finally diff 補償：存入 N → 驗代理 +N → 提取 N 還原 → 驗回初始；
中途失敗時 finally 依差額補回，確保 qaautodrf 額度不留殘差、可重跑。

target = site_config.dashboard_agent_user（= qaautodrf，站長直屬下線、與既有代理 smoke 同帳號）。
"""

import pytest
from playwright.sync_api import Page

from pages.dashboard.factory import get_dashboard_management_page_class

AMOUNT = 1  # 派點/收點對稱金額；小額避免影響業務


@pytest.mark.p1
@pytest.mark.rf
@pytest.mark.dashboard
@pytest.mark.wallet
class TestMasterToAgentTopUp:
    """RF-DASH-MASTER-TOPUP-001：總代對代理存入/提取額度驗證（只驗代理側，總代 ∞）。"""

    def test_master_deposit_withdraw_to_agent(self, fresh_dashboard_page: Page, site_config):
        page = fresh_dashboard_page
        Mgmt = get_dashboard_management_page_class(site_config.site_id)
        mgmt = Mgmt(page)
        agent = site_config.dashboard_agent_user  # qaautodrf，不寫死帳號

        # 站長落點即 #/management/all-management；切代理 tab + 開大每頁筆數
        page.goto(
            f"{site_config.dashboard_url}#/management/all-management",
            wait_until="domcontentloaded",
        )
        page.locator(".sidebar-nav").first.wait_for(state="attached", timeout=15000)
        mgmt.switch_to_agent_tab()
        mgmt.set_page_size(500)

        before = mgmt.get_agent_balance(agent)
        print(f"\n[rf-master-topup] {agent} before balance={before}")

        try:
            # --- 存入（總代派點給代理）N ---
            mgmt.deposit_to_agent(agent, AMOUNT)
            after_dep = mgmt.get_agent_balance(agent)
            print(f"[rf-master-topup] after deposit={after_dep}")
            assert after_dep == pytest.approx(before + AMOUNT, abs=0.01), (
                f"總代存入 {AMOUNT} 後 {agent} 餘額應為 {before + AMOUNT}，實得 {after_dep}"
            )

            # --- 提取（總代收回）N，還原 ---
            mgmt.withdraw_from_agent(agent, AMOUNT)
            after_wd = mgmt.get_agent_balance(agent)
            print(f"[rf-master-topup] after withdraw={after_wd}")
            assert after_wd == pytest.approx(before, abs=0.01), (
                f"總代提取 {AMOUNT} 後 {agent} 餘額應回到初始 {before}，實得 {after_wd}"
            )
        finally:
            # 保險補償：把代理餘額拉回 before（diff=0 則 no-op）。best-effort，不遮蔽原始失敗。
            try:
                cur = mgmt.get_agent_balance(agent)
                diff = round(cur - before)
                if diff > 0:
                    mgmt.withdraw_from_agent(agent, abs(diff))
                    print(f"[rollback] 提取補償 {abs(diff)} → 還原至 {before}")
                elif diff < 0:
                    mgmt.deposit_to_agent(agent, abs(diff))
                    print(f"[rollback] 存入補償 {abs(diff)} → 還原至 {before}")
            except Exception as e:  # noqa: BLE001 — 補償 best-effort，僅警告
                print(f"[rollback warning] 補償未完成：{type(e).__name__}: {e}")
