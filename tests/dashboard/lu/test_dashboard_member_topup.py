"""
LU 後台 — 站長會員主錢包額度調整（測試專用充值路徑）

⚠️ 帳號層級：**站長帳號**（SITE_LU_DASHBOARD_USER）。實機 probe（2026-06-25）確認此能力
   站長專屬；代理點主錢包金額不會開彈窗（Game wallet/Send points 亦 disabled）。

非正規金流：正規流程「代理派點 → 站長補單」因代理無點數卡住（見 dashboard onboarding
defer 紀錄）。此處走後台「會員管理 → Main wallet 金額彈窗 → 額度調整」直接增減，為測試需求作法。

對稱可逆（CLAUDE.md：state-mutating 測試須可逆）：
  增加 N → 驗餘額 +N → 減少 N 還原 → 驗回原值；finally 以 diff 補償保證即使中途失敗也還原。

額度歷史稽核：增/減操作各應在「會員報表 > Amount adjustment」(#/report/balance-adjustment-report)
  產生一筆對應紀錄；以唯一 token remark 精準鎖定，驗證 member/amount/type/結餘。

排序：本檔（member_topup）字母序在 test_dashboard_navigation.py（含終結 session 的 logout）
之前，故能在 session 仍存活時操作站長 dashboard_page。
"""

import uuid

import pytest
from playwright.sync_api import Page

from pages.dashboard.factory import get_dashboard_management_page_class

TARGET_MEMBER = "norautolu1"   # 站長底下的測試會員（代理 norauto001 之下線）
ADJUST = 1                     # 調整額度（取最小值，降低對測試資料的擾動）


@pytest.mark.p1
@pytest.mark.lu
@pytest.mark.dashboard
@pytest.mark.wallet
class TestMasterMainWalletTopup:
    """LU-DASH-004：站長主錢包額度調整，對稱可逆。"""

    def test_main_wallet_adjust_reversible(self, dashboard_page: Page, site_config):
        Mgmt = get_dashboard_management_page_class(site_config.site_id)
        mgmt = Mgmt(dashboard_page)

        # 唯一 token：讓額度歷史驗證能精準鎖定本次產生的紀錄（避開歷史殘留同文案）
        token = uuid.uuid4().hex[:8]
        remark_inc = f"autoreg-{token}-inc"
        remark_dec = f"autoreg-{token}-dec"

        mgmt.goto_member_management(site_config.dashboard_url)
        mgmt.search_member(TARGET_MEMBER)
        before = mgmt.get_member_wallet_amount(TARGET_MEMBER)

        try:
            # --- 增加 N ---
            mgmt.open_main_wallet_dialog(TARGET_MEMBER)
            # 彈窗 Balance 應等於列表顯示值（同一資料源，順帶驗證鎖對會員）
            assert mgmt.dialog_balance() == before, (
                f"彈窗 Balance({mgmt.dialog_balance()}) 與列表金額({before}) 不一致，疑鎖錯會員"
            )
            mgmt.adjust_main_wallet("increase", ADJUST, remark=remark_inc)

            mgmt.search_member(TARGET_MEMBER)
            after_inc = mgmt.get_member_wallet_amount(TARGET_MEMBER)
            assert after_inc == before + ADJUST, (
                f"增加後餘額不符：{before} + {ADJUST} 期望 {before + ADJUST}，實得 {after_inc}"
            )

            # --- 減少 N 還原 ---
            mgmt.open_main_wallet_dialog(TARGET_MEMBER)
            mgmt.adjust_main_wallet("reduce", ADJUST, remark=remark_dec)

            mgmt.search_member(TARGET_MEMBER)
            after_red = mgmt.get_member_wallet_amount(TARGET_MEMBER)
            assert after_red == before, (
                f"還原後餘額不符：期望 {before}，實得 {after_red}"
            )

            # --- 額度歷史：增/減各產生一筆對應稽核紀錄 ---
            mgmt.goto_balance_adjustment_report(site_config.dashboard_url)

            rec_inc = mgmt.get_adjustment_record(remark_inc)
            assert rec_inc is not None, f"額度歷史找不到增加紀錄（remark={remark_inc}）"
            assert rec_inc["member"] == TARGET_MEMBER, f"增加紀錄會員不符：{rec_inc}"
            assert rec_inc["amount"] == ADJUST, f"增加紀錄金額不符：{rec_inc}"
            assert "increase" in rec_inc["type"].lower(), f"增加紀錄類型不符：{rec_inc}"
            assert rec_inc["end_balance"] == before + ADJUST, f"增加紀錄結餘不符：{rec_inc}"

            rec_dec = mgmt.get_adjustment_record(remark_dec)
            assert rec_dec is not None, f"額度歷史找不到減少紀錄（remark={remark_dec}）"
            assert rec_dec["amount"] == -ADJUST, f"減少紀錄金額不符：{rec_dec}"
            assert "reduce" in rec_dec["type"].lower(), f"減少紀錄類型不符：{rec_dec}"
            assert rec_dec["end_balance"] == before, f"減少紀錄結餘不符：{rec_dec}"
        finally:
            # 保險補償：不論前面成功與否，把餘額拉回 before（diff=0 則 no-op）。
            # best-effort：失敗只印警告、不遮蔽原始 assert 失敗訊息（不可 except: pass）。
            # 先導回會員管理頁（前面可能停在額度歷史頁，欄位結構不同）。
            try:
                mgmt.goto_member_management(site_config.dashboard_url)
                mgmt.search_member(TARGET_MEMBER)
                cur = mgmt.get_member_wallet_amount(TARGET_MEMBER)
                diff = round(cur - before)
                if diff != 0:
                    mgmt.open_main_wallet_dialog(TARGET_MEMBER)
                    mode = "reduce" if diff > 0 else "increase"
                    mgmt.adjust_main_wallet(mode, abs(diff), remark="auto-reg rollback")
                    print(f"[rollback] 補償 {mode} {abs(diff)} → 還原至 {before}")
            except Exception as e:  # noqa: BLE001 — 補償失敗僅警告，保留原始失敗
                print(f"[rollback warning] 補償未完成：{type(e).__name__}: {e}")
