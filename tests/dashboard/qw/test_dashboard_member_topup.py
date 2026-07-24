"""
QW 後台 — 站長會員主錢包額度調整（測試專用充值路徑）

⚠️ 帳號層級：**站長帳號**（SITE_QW_DASHBOARD_USER）。QW dashboard POM re-export LU，
   主錢包充值流程與 LU 同構（probe 2026-06-25：會員（SITE_QW_USERNAME）Main wallet 欄 index 5、
   點金額開「Main wallet」彈窗）。

非正規金流：走後台「會員管理 → Main wallet 金額彈窗 → 額度調整」直接增減，為測試需求作法。

對稱可逆：增加 N → 驗 +N → 減少 N 還原 → 驗回原值；finally diff 補償保證即使中途失敗也還原。
額度歷史稽核：增/減各應在「會員報表 > Amount adjustment」(#/report/balance-adjustment-report)
  產生一筆對應紀錄；以唯一 token remark 精準鎖定。

目標會員用 site_config.username（SITE_QW_USERNAME，站長底下穩定會員）。
"""

import uuid

import pytest
from playwright.sync_api import Page

from pages.dashboard.factory import get_dashboard_management_page_class

ADJUST = 1  # 調整額度（最小值，降低對測試資料的擾動）


@pytest.mark.p1
@pytest.mark.qw
@pytest.mark.dashboard
@pytest.mark.wallet
class TestMasterMainWalletTopup:
    """QW-DASH-TOPUP-001：站長主錢包額度調整，對稱可逆 + 額度歷史稽核。"""

    def test_main_wallet_adjust_reversible(self, dashboard_page: Page, site_config):
        Mgmt = get_dashboard_management_page_class(site_config.site_id)
        mgmt = Mgmt(dashboard_page)
        target = site_config.username  # SITE_QW_USERNAME，不寫死帳號

        token = uuid.uuid4().hex[:8]
        remark_inc = f"autoreg-{token}-inc"
        remark_dec = f"autoreg-{token}-dec"

        mgmt.goto_member_management(site_config.dashboard_url)
        mgmt.search_member(target)
        before = mgmt.get_member_wallet_amount(target)

        try:
            # --- 增加 N ---
            mgmt.open_main_wallet_dialog(target)
            assert mgmt.dialog_balance() == before, (
                f"彈窗 Balance({mgmt.dialog_balance()}) 與列表金額({before}) 不一致，疑鎖錯會員"
            )
            mgmt.adjust_main_wallet("increase", ADJUST, remark=remark_inc)

            mgmt.search_member(target)
            after_inc = mgmt.get_member_wallet_amount(target)
            assert after_inc == before + ADJUST, (
                f"增加後餘額不符：{before} + {ADJUST} 期望 {before + ADJUST}，實得 {after_inc}"
            )

            # --- 減少 N 還原 ---
            mgmt.open_main_wallet_dialog(target)
            mgmt.adjust_main_wallet("reduce", ADJUST, remark=remark_dec)

            mgmt.search_member(target)
            after_red = mgmt.get_member_wallet_amount(target)
            assert after_red == before, f"還原後餘額不符：期望 {before}，實得 {after_red}"

            # --- 額度歷史：增/減各一筆稽核紀錄 ---
            mgmt.goto_balance_adjustment_report(site_config.dashboard_url)

            rec_inc = mgmt.get_adjustment_record(remark_inc)
            assert rec_inc is not None, f"額度歷史找不到增加紀錄（remark={remark_inc}）"
            assert rec_inc["member"] == target, f"增加紀錄會員不符：{rec_inc}"
            assert rec_inc["amount"] == ADJUST, f"增加紀錄金額不符：{rec_inc}"
            assert "increase" in rec_inc["type"].lower(), f"增加紀錄類型不符：{rec_inc}"
            assert rec_inc["end_balance"] == before + ADJUST, f"增加紀錄結餘不符：{rec_inc}"

            rec_dec = mgmt.get_adjustment_record(remark_dec)
            assert rec_dec is not None, f"額度歷史找不到減少紀錄（remark={remark_dec}）"
            assert rec_dec["amount"] == -ADJUST, f"減少紀錄金額不符：{rec_dec}"
            assert "reduce" in rec_dec["type"].lower(), f"減少紀錄類型不符：{rec_dec}"
            assert rec_dec["end_balance"] == before, f"減少紀錄結餘不符：{rec_dec}"
        finally:
            # 保險補償：把餘額拉回 before（diff=0 則 no-op）。best-effort，不遮蔽原始失敗。
            try:
                mgmt.goto_member_management(site_config.dashboard_url)
                mgmt.search_member(target)
                cur = mgmt.get_member_wallet_amount(target)
                diff = round(cur - before)
                if diff != 0:
                    mgmt.open_main_wallet_dialog(target)
                    mode = "reduce" if diff > 0 else "increase"
                    mgmt.adjust_main_wallet(mode, abs(diff), remark="auto-reg rollback")
                    print(f"[rollback] 補償 {mode} {abs(diff)} → 還原至 {before}")
            except Exception as e:  # noqa: BLE001 — 補償 best-effort，僅警告
                print(f"[rollback warning] 補償未完成：{type(e).__name__}: {e}")
