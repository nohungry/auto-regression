"""
QW 後台 — 站長「一般存款」（General deposit）

既有 test_dashboard_member_topup.py 走 Main wallet 彈窗的**額度調整**（increase /
reduce）；本檔走同一彈窗的第三種模式 **General deposit（value=3，一般存款）**——
那是最接近真實存款單的後台路徑，先前只在 POM 的 WALLET_ADJUST_MODES 裡定義、
從未被任何測試執行過。

實機 probe（2026-08-10）：切到 General deposit 後，後台會非同步回填 **Platform bank**
下拉（dev 環境三個渠道，自動預選第一項＝後台補單渠道），Member bank 維持 None。
無 HTML required 屬性，但仍須等下拉回填完再送出，否則會在渠道未定時 Confirm。

對稱可逆（D-015）：一般存款 N → 驗餘額 +N → 以額度調整-減少 N 還原 → 驗回原值；
finally 以 diff 補償，保證中途失敗也還原（沿用 member_topup 已驗證的作法）。

⚠️ **本檔攔到一個產品缺陷（bug 清單 #13）**：一般存款確實改動會員餘額，卻**不在任何
金流報表留下紀錄**（9 個金流頁全查無）。故拆成兩條：
  1. test_general_deposit_reversible —— 驗金額真的動了且可還原（綠）
  2. test_general_deposit_leaves_audit_record —— 驗留痕，xfail(strict)，產品補上稽核
     紀錄後會自動 XPASS 提醒 un-gate

排序：本檔字母序在 test_zz_dashboard_logout.py 之前，故 session dashboard_page 仍存活。
"""

import uuid

import pytest
from playwright.sync_api import Page

from pages.dashboard.factory import get_dashboard_management_page_class

ADJUST = 1  # 存款金額取最小值，降低對共用測試資料的擾動


def _resolve_target(site_config):
    """目標會員；未設定則 skip（帳號依 D-014 不進 repo）。"""
    target = site_config.username
    if not target:
        pytest.skip("SITE_QW_USERNAME 未設定（.env），無法指定目標會員")
    return target


def _restore_balance(mgmt, site_config, target, before):
    """保險補償：把餘額拉回 before（diff=0 則 no-op）。

    best-effort：失敗只印警告、不遮蔽原始 assert 失敗訊息（不可 except: pass）。
    """
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
    except Exception as e:  # noqa: BLE001 — 補償失敗僅警告，保留原始失敗
        print(f"[rollback warning] 補償未完成：{type(e).__name__}: {e}")


@pytest.mark.p1
@pytest.mark.qw
@pytest.mark.dashboard
@pytest.mark.wallet
class TestGeneralDeposit:
    """QW-DASH-DEPOSIT-001：站長一般存款改動餘額，且對稱可逆。"""

    def test_general_deposit_reversible(self, dashboard_page: Page, site_config):
        Mgmt = get_dashboard_management_page_class(site_config.site_id)
        mgmt = Mgmt(dashboard_page)
        target = _resolve_target(site_config)

        token = uuid.uuid4().hex[:8]
        remark_dep = f"autoreg-{token}-gdep"
        remark_red = f"autoreg-{token}-gred"

        mgmt.goto_member_management(site_config.dashboard_url)
        mgmt.search_member(target)
        before = mgmt.get_member_wallet_amount(target)

        try:
            # --- 一般存款 N ---
            mgmt.open_main_wallet_dialog(target)
            assert mgmt.dialog_balance() == before, (
                f"彈窗 Balance({mgmt.dialog_balance()}) 與列表金額({before}) 不一致，疑鎖錯會員"
            )
            # 切到 General deposit 後 Platform bank 才會有渠道可選（回填前送出＝渠道未定）
            mgmt.adjust_main_wallet("deposit", ADJUST, remark=remark_dep)

            mgmt.search_member(target)
            after_dep = mgmt.get_member_wallet_amount(target)
            assert after_dep == before + ADJUST, (
                f"一般存款後餘額不符：{before} + {ADJUST} 期望 {before + ADJUST}，實得 {after_dep}"
            )

            # --- 額度調整-減少 N 還原 ---
            mgmt.open_main_wallet_dialog(target)
            mgmt.adjust_main_wallet("reduce", ADJUST, remark=remark_red)

            mgmt.search_member(target)
            after_red = mgmt.get_member_wallet_amount(target)
            assert after_red == before, f"還原後餘額不符：期望 {before}，實得 {after_red}"

            # 還原這一筆（額度調整）**有**留痕，順帶守住既有稽核能力沒退化。
            # 其起始餘額 = before + ADJUST，正是「存款確實入帳」的獨立佐證。
            mgmt.goto_balance_adjustment_report(site_config.dashboard_url)
            rec = mgmt.get_adjustment_record(remark_red)
            assert rec is not None, f"額度歷史找不到還原紀錄（remark={remark_red}）"
            assert rec["amount"] == -ADJUST, f"還原紀錄金額不符：{rec}"
            assert rec["end_balance"] == before, f"還原紀錄結餘不符：{rec}"
        finally:
            _restore_balance(mgmt, site_config, target, before)


@pytest.mark.p1
@pytest.mark.qw
@pytest.mark.dashboard
@pytest.mark.wallet
class TestGeneralDepositAudit:
    """QW-DASH-DEPOSIT-002：一般存款應在金流報表留下稽核紀錄。"""

    @pytest.mark.xfail(
        strict=True,
        reason=(
            "產品缺陷（bug 清單 #13）：後台「一般存款」會改動會員主錢包餘額，"
            "卻不在任何金流報表留下紀錄。2026-08-10 實測：存款 +1 使餘額 1000→1001"
            "（由後續額度調整紀錄的起始餘額 1001 獨立佐證），但以唯一 remark token "
            "搜遍 9 個金流頁（wallet-history / member-deposit / balance-adjustment / "
            "deposit-payment / point records / 存提審核頁）全數查無。"
            "動錢不留痕＝稽核斷點。產品補上紀錄後本條會 XPASS 提醒 un-gate。"
        ),
    )
    def test_general_deposit_leaves_audit_record(self, dashboard_page: Page, site_config):
        """存款後以唯一 token 搜遍所有金流稽核落點，應至少有一處留痕。"""
        Mgmt = get_dashboard_management_page_class(site_config.site_id)
        mgmt = Mgmt(dashboard_page)
        target = _resolve_target(site_config)

        token = uuid.uuid4().hex[:8]
        remark_dep = f"autoreg-{token}-audit"

        mgmt.goto_member_management(site_config.dashboard_url)
        mgmt.search_member(target)
        before = mgmt.get_member_wallet_amount(target)

        try:
            mgmt.open_main_wallet_dialog(target)
            mgmt.adjust_main_wallet("deposit", ADJUST, remark=remark_dep)

            mgmt.search_member(target)
            after = mgmt.get_member_wallet_amount(target)
            assert after == before + ADJUST, (
                f"前置條件不成立：存款未入帳（期望 {before + ADJUST}，實得 {after}）"
            )

            hit = mgmt.find_audit_record_route(site_config.dashboard_url, remark_dep)
            assert hit is not None, (
                f"一般存款（remark={remark_dep}，金額 {ADJUST}，餘額 {before}→{after}）"
                f"未在任何金流報表留下紀錄：{list(Mgmt.MONEY_FLOW_AUDIT_ROUTES)}"
            )
        finally:
            _restore_balance(mgmt, site_config, target, before)
