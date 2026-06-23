"""
RF 後台會員充值測試（存入/提取）— 金爺娛樂城（信用版）
RF-DASH-TOPUP-001

使用站長帳號 SITE_RF_DASHBOARD_USER（qatest03）登入後台，
對會員 drfauto01（上級代理 qaautodrf）進行存入與提取操作，
驗證會員額度正確增減。

Rollback 設計（對稱還原 + try/finally 補償）：
- 存入 AMOUNT → 驗額度 +AMOUNT → 提取 AMOUNT → 驗額度回初始。
- 若存入後 assert 失敗（或 assert 前拋例外），finally 執行補償提取，
  確保 drfauto01 額度不留殘差，下次測試可重跑。
- 連跑兩次 idempotent：每次測試結束後額度應與測試前相同。

技術要點：
- 會員列表為 .tab-item 結構（非 table/tr），設 500 筆確保 drfauto01（第 40 筆）在 DOM 中。
- 無帳號搜尋框；用 locator filter 直接定位 .tab-item。
- get_member_balance 透過打開存入 dialog 讀取 span.label-xs（實時值），取消後回到列表。
- RF 後台無操作者密碼欄位（不同於 RC 站）。
- 使用 go_dashboard fixture 確保測試前回到 #/management/all-management，
  避免 session-scoped page 殘留在其他頁面（navigation smoke 測試後）。
"""

import pytest
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from pages.dashboard.factory import get_dashboard_management_page_class


AMOUNT = 1  # 存入/提取對稱金額，測試結束額度應回到初始值；用小額避免影響業務


@pytest.mark.p1
@pytest.mark.rf
@pytest.mark.dashboard
@pytest.mark.wallet
class TestMemberTopUp:
    """RF-DASH-TOPUP-001：後台會員存入/提取額度驗證"""

    def test_deposit_and_withdraw(self, fresh_dashboard_page, site_config):
        """RF-DASH-TOPUP-001：存入 1 → 驗額度 +1 → 提取 1 → 驗額度回到初始（含 finally rollback）。

        使用 fresh_dashboard_page fixture（function-scoped，獨立登入），
        避免 session-scoped dashboard_page 被 logout smoke 測試污染。

        斷言策略：
        - before/after 額度用 pytest.approx(abs=0.01) 比對，不寫死特定數值。
        - get_member_balance 從存入 dialog 的 span.label-xs 讀取實時值，截圖 label 帶
          「非空」關鍵字（label 中的值僅供 review，不代表寫死比對）。
        """
        dashboard_page = fresh_dashboard_page
        ManagementPage = get_dashboard_management_page_class(site_config.site_id)
        mgmt = ManagementPage(dashboard_page)
        member_account = site_config.username  # SITE_RF_USERNAME（= drfauto01），不寫死帳號

        # 1. 切到會員 tab
        mgmt.switch_to_member_tab()

        # 2. 設每頁 500 筆，確保 drfauto01 在 DOM 中
        mgmt.set_page_size(500)

        # 3. 記錄存入前額度（動態值，不寫死；截圖 label 標明「非空」）
        balance_before = mgmt.get_member_balance(member_account)
        print(f"\n[topup] {member_account} before balance={balance_before}")

        deposit_done = False
        try:
            # 4. 存入 1
            mgmt.deposit(member_account, AMOUNT)
            deposit_done = True

            # 5. 回到管理頁重設狀態，確保 dialog 關閉後列表重新渲染
            mgmt.reload_management_page(site_config.dashboard_url)
            mgmt.switch_to_member_tab()
            mgmt.set_page_size(500)

            # 6. 驗額度增加（透過打開/關閉 dialog 讀實時值）
            balance_after_deposit = mgmt.get_member_balance(member_account)
            print(f"[topup] after deposit balance={balance_after_deposit}")
            assert balance_after_deposit == pytest.approx(balance_before + AMOUNT, abs=0.01), (
                f"存入 {AMOUNT} 後 {member_account} 額度應為 {balance_before + AMOUNT:.2f}，"
                f"實際為 {balance_after_deposit:.2f}"
            )

            # 7. 提取 1（對稱還原，將額度回到初始）
            mgmt.withdraw(member_account, AMOUNT)
            deposit_done = False  # withdraw 已抵銷 deposit，無需 finally rollback

            # 8. 回到管理頁重設狀態
            mgmt.reload_management_page(site_config.dashboard_url)
            mgmt.switch_to_member_tab()
            mgmt.set_page_size(500)

            # 9. 驗額度回到初始
            balance_after_withdraw = mgmt.get_member_balance(member_account)
            print(f"[topup] after withdraw balance={balance_after_withdraw}")
            assert balance_after_withdraw == pytest.approx(balance_before, abs=0.01), (
                f"提取 {AMOUNT} 後 {member_account} 額度應回到初始 {balance_before:.2f}，"
                f"實際為 {balance_after_withdraw:.2f}"
            )

        finally:
            # Rollback：存入完成但提取未完成時（assertion 失敗或中途拋例外），補償提取
            if deposit_done:
                try:
                    # 確保在管理頁且會員 tab 已顯示
                    mgmt.reload_management_page(site_config.dashboard_url)
                    mgmt.switch_to_member_tab()
                    mgmt.set_page_size(500)
                    mgmt.withdraw(member_account, AMOUNT)
                except PlaywrightTimeoutError:
                    pass  # best-effort，不遮蔽原始測試錯誤
