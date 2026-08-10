"""
LU 後台登出（站長 + 代理層級）

⚠️ 檔名 `zz` 前綴是**刻意的排序控制**，不是命名隨意：
   登出會終結 session-scoped 的 `dashboard_page`，而 pytest 依檔名字母序收集，
   任何字母序在後、又依賴同一個 session fixture 的測試都會拿到已登出的 page。
   本檔原本併在 `test_dashboard_navigation.py`，導致字母序在後的
   `test_menu_entries.py` 全目錄跑時固定失敗（2026-08-10 實跑確認：12 passed /
   1 failed，單檔跑則綠，所以一直沒被發現）。拆出並前綴 zz 後，「終結 session」
   永遠是最後一步。新增依賴 `dashboard_page` 的測試檔不必再擔心排序。

   刻意不另起 fresh-login fixture：與 session 同帳號會互踢（見 single-session 規則）。
"""

import pytest
from playwright.sync_api import Page

from pages.dashboard.factory import get_dashboard_management_page_class


@pytest.mark.p1
@pytest.mark.lu
@pytest.mark.dashboard
class TestDashboardLogout:
    """LU-DASH-003：後台登出回登入頁。"""

    def test_logout_returns_to_login(self, dashboard_page: Page, site_config):
        """點使用者選單 → Logout → 回 #/login，登入表單重現。"""
        Mgmt = get_dashboard_management_page_class(site_config.site_id)
        mgmt = Mgmt(dashboard_page)
        mgmt.logout()
        assert "/login" in dashboard_page.url, f"登出後未回登入頁：{dashboard_page.url}"


@pytest.mark.p1
@pytest.mark.lu
@pytest.mark.dashboard
class TestAgentDashboardLogout:
    """LU-DASH-AGENT-003：代理登出回登入頁。

    使用 session agent_dashboard_page 並定義在導航之後 → 全域最後執行；
    登出終結 session，後面不可再有依賴該 session 的測試。
    """

    def test_logout_returns_to_login(self, agent_dashboard_page: Page, site_config):
        """點使用者選單 → Logout → 回 #/login，登入表單重現。"""
        Mgmt = get_dashboard_management_page_class(site_config.site_id)
        mgmt = Mgmt(agent_dashboard_page)
        mgmt.logout()
        assert "/login" in agent_dashboard_page.url, (
            f"代理登出後未回登入頁：{agent_dashboard_page.url}"
        )
