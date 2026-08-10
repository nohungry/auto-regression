"""
LU 跨前後台餘額一致性（後台調整 → 前台看得到）

落實 docs/dashboard-technical-notes.md 規則 9 一直沒實作的那一層：
「餘額驗證採 UI + API 雙重確認…前台登入查看錢包留給跨前後台 e2e 測試（較重）」。

先前現金版的後台 top_up 測試只在**後台自己的列表**驗餘額變化 —— 後台顯示對了，
不代表會員在前台看到的錢是對的（兩邊可能讀不同資料源 / 前台有快取）。本檔把這條
縫補起來：後台站長調整額度 → 前台會員 reload → 驗前台餘額同步變化 → 後台還原 →
驗前台回到原值。

帳號：前台 = SITE_LU_USERNAME（class_logged_in_page，站點 conftest 已指向本站），
後台 = SITE_LU_DASHBOARD_USER 站長（dashboard_page）。**兩者不同帳號故不互踢**
（同帳號不可並行，見 single-session 規則）；目標會員即前台帳號本人，
2026-08-10 實測三站的前台帳號皆可在站長後台會員管理搜到。

對稱可逆（D-015）：+N → 驗 → -N 還原 → 驗；finally 以 diff 補償。

排序：本檔字母序在 test_zz_dashboard_logout.py 之前，故 session dashboard_page 仍存活。
"""

import re

import pytest
from playwright.sync_api import Page

from pages.dashboard.factory import get_dashboard_management_page_class
from pages.factory import get_home_page_class
from utils.screenshot_helper import get_screenshotter
from utils.wait_helpers import wait_for_text_matches

HomePage = get_home_page_class("lu")

ADJUST = 1  # 調整額度取最小值，降低對共用測試資料的擾動


def _parse_balance(text: str) -> float:
    """前台餘額文字 → float。各站前綴/千分位不一（如 '$1,000' / '1000'），只取數字部分。"""
    m = re.search(r"[\d,]+(?:\.\d+)?", text)
    assert m, f"前台餘額文字取不到數字：{text!r}"
    return float(m.group(0).replace(",", ""))


def _amount_pattern(value: float) -> "re.Pattern":
    """金額 → 容忍千分位的比對 pattern（1001 同時匹配 '1001' 與 '1,001'）。

    各站是否加千分位不一致（實測 LG 顯示 '1001' 無逗號），寫死格式會誤判成
    「前台沒同步」。逗號位置一律設為選擇性。
    """
    return re.compile(",?".join(str(int(value))))


def _read_frontend_balance(page: Page, expect_amount=None) -> float:
    """回首頁 reload 後讀前台餘額。

    expect_amount 給定時先等文字出現該數字再讀 —— 前台餘額為非同步取得，
    reload 後直接讀會拿到舊值或空值（可判定等待，取代硬等）。
    """
    home = HomePage(page)
    page.reload(wait_until="domcontentloaded")
    home.dismiss_any_popups()
    pattern = _amount_pattern(expect_amount) if expect_amount is not None else re.compile(r"\d")
    wait_for_text_matches(home.balance, pattern, timeout=20000)
    return _parse_balance(home.balance.inner_text())


@pytest.mark.p1
@pytest.mark.lu
@pytest.mark.dashboard
@pytest.mark.wallet
class TestFrontendBalanceSync:
    """LU-DASH-SYNC-001：後台調整額度後，前台會員餘額同步反映且可還原。"""

    def test_backend_adjust_reflects_on_frontend(
        self, dashboard_page: Page, class_logged_in_page: Page, site_config
    ):
        Mgmt = get_dashboard_management_page_class(site_config.site_id)
        mgmt = Mgmt(dashboard_page)
        fe = class_logged_in_page
        sh = get_screenshotter(fe)
        target = site_config.username

        # --- 基準：前台與後台餘額應一致（同一資料源的第一道驗證）---
        fe_before = _read_frontend_balance(fe)
        if sh: sh.capture(HomePage(fe).balance, f"verify_前台餘額_調整前_{fe_before}")

        mgmt.goto_member_management(site_config.dashboard_url)
        mgmt.search_member(target)
        be_before = mgmt.get_member_wallet_amount(target)
        assert fe_before == be_before, (
            f"前後台餘額基準不一致：前台 {fe_before} vs 後台 {be_before}"
        )

        try:
            # --- 後台 +N → 前台應看到 +N ---
            mgmt.open_main_wallet_dialog(target)
            mgmt.adjust_main_wallet("increase", ADJUST, remark="autoreg-sync-inc")

            fe_after = _read_frontend_balance(fe, expect_amount=fe_before + ADJUST)
            if sh: sh.capture(HomePage(fe).balance, f"verify_前台餘額_調整後_{fe_after}")
            assert fe_after == fe_before + ADJUST, (
                f"後台 +{ADJUST} 後前台餘額未同步：期望 {fe_before + ADJUST}，實得 {fe_after}"
            )

            # --- 後台 -N 還原 → 前台應回到原值 ---
            mgmt.search_member(target)
            mgmt.open_main_wallet_dialog(target)
            mgmt.adjust_main_wallet("reduce", ADJUST, remark="autoreg-sync-dec")

            fe_restored = _read_frontend_balance(fe, expect_amount=fe_before)
            if sh: sh.capture(HomePage(fe).balance, f"verify_前台餘額_還原後_{fe_restored}")
            assert fe_restored == fe_before, (
                f"還原後前台餘額不符：期望 {fe_before}，實得 {fe_restored}"
            )
        finally:
            # 保險補償：以後台為準把餘額拉回 be_before（diff=0 則 no-op）。
            # best-effort：失敗只印警告、不遮蔽原始 assert 失敗訊息（不可 except: pass）。
            try:
                mgmt.goto_member_management(site_config.dashboard_url)
                mgmt.search_member(target)
                cur = mgmt.get_member_wallet_amount(target)
                diff = round(cur - be_before)
                if diff != 0:
                    mgmt.open_main_wallet_dialog(target)
                    mode = "reduce" if diff > 0 else "increase"
                    mgmt.adjust_main_wallet(mode, abs(diff), remark="auto-reg rollback")
                    print(f"[rollback] 補償 {mode} {abs(diff)} → 還原至 {be_before}")
            except Exception as e:  # noqa: BLE001 — 補償失敗僅警告，保留原始失敗
                print(f"[rollback warning] 補償未完成：{type(e).__name__}: {e}")
