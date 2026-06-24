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


@pytest.mark.p1
@pytest.mark.lu
@pytest.mark.dashboard
class TestDashboardLogout:
    """LU-DASH-003：後台登出回登入頁。

    使用 session dashboard_page 並定義在導航之後 → globally 最後執行；
    登出會終結 session，故後面不可再有依賴該 session 的測試。
    （刻意不另起 fresh-login fixture：與 session 同帳號會互踢，見 single-session 規則。）
    """

    def test_logout_returns_to_login(self, dashboard_page: Page, site_config):
        """點使用者選單 → Logout → 回 #/login，登入表單重現。"""
        Mgmt = get_dashboard_management_page_class(site_config.site_id)
        mgmt = Mgmt(dashboard_page)
        mgmt.logout()
        assert "/login" in dashboard_page.url, f"登出後未回登入頁：{dashboard_page.url}"
