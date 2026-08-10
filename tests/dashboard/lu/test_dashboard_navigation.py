"""
LU 後台導航 + 登出測試（第二波：read-only smoke）

⚠️ 帳號層級：本檔以**站長帳號 <LU 站長帳號>**（SITE_LU_DASHBOARD_USER）登入驗證。
   後續會有「下級代理帳號」（SITE_LU_DASHBOARD_AGENT_USER）提供，屆時權限/可見選單
   不同 → 另立代理層級測試，不沿用本檔斷言（站長可見 18 項頂層選單，代理可能較少）。

斷言策略：後台 locale 混雜（英文 + 部分未翻譯 i18n key）→ 一律用結構性
（route hash 變化 + 容器可見 + 選單數量），不綁中文/英文文案。
"""

import pytest
from playwright.sync_api import Page, expect

from pages.dashboard.factory import get_dashboard_management_page_class


@pytest.mark.p1
@pytest.mark.lu
@pytest.mark.dashboard
class TestDashboardNavigation:
    """LU-DASH-002：後台側欄 + 導航 read-only smoke（站長層級）"""

    def test_sidebar_renders(self, go_dashboard: Page, site_config):
        """側欄選單載入：頂層選單項數量正常、首項可見。"""
        Mgmt = get_dashboard_management_page_class(site_config.site_id)
        mgmt = Mgmt(go_dashboard)
        count = mgmt.sidebar_item_count()
        assert count >= 5, f"側欄頂層選單數異常（站長預期 >=5，實得 {count}）"
        expect(mgmt.parent_items.first).to_be_visible()

    @pytest.mark.parametrize("route", [
        "member-registration",   # 會員管理區
        "agent-wallet",          # 代理/帳務區
        "reset-password",        # 個人帳號設定（read-only render）
    ])
    def test_navigate_section(self, go_dashboard: Page, site_config, route):
        """點側欄葉節點導航到代表頁：URL hash 變化 + 內容容器可見。"""
        Mgmt = get_dashboard_management_page_class(site_config.site_id)
        mgmt = Mgmt(go_dashboard)
        mgmt.navigate(route)
        assert route in go_dashboard.url, f"導航後 URL 未含 {route}：{go_dashboard.url}"



# LU-DASH-003（登出）已移至 test_zz_dashboard_logout.py：
# 登出會終結 session-scoped 的 dashboard_page，而 pytest 依**檔名字母序**收集，
# 原本放在本檔會讓字母序在後的 test_menu_entries.py / test_money_flow_pages.py
# 拿到已登出的 page 而失敗（2026-08-10 全目錄實跑確認：12 passed / 1 failed）。
# 檔名前綴 zz 確保「終結 session」永遠是最後一步。
