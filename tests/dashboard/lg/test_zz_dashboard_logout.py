"""
LG 後台登出（代理層級）

⚠️ 檔名 `zz` 前綴是**刻意的排序控制**，不是命名隨意：
   登出會終結 session-scoped 的後台 page fixture，而 pytest 依檔名字母序收集，
   任何字母序在後、又依賴同一個 session fixture 的測試都會拿到已登出的 page。
   拆檔前 LG 全目錄跑即固定失敗（test_dashboard_agent.py 的登出先跑，
   test_menu_entries.py 的代理層級測試隨後拿到已登出 page）；單檔跑則綠，
   所以一直沒被發現。前綴 zz 後「終結 session」永遠是最後一步，
   新增依賴這些 fixture 的測試檔不必再擔心排序。

   刻意不另起 fresh-login fixture：與 session 同帳號會互踢（見 single-session 規則）。
"""

import pytest
from playwright.sync_api import Page

from pages.dashboard.factory import get_dashboard_management_page_class


@pytest.mark.p1
@pytest.mark.lg
@pytest.mark.dashboard
class TestAgentDashboardLogout:
    """LG-DASH-AGENT-003：代理登出回登入頁。

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
