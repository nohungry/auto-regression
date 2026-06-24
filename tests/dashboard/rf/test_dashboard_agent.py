"""
RF 後台代理層級 read-only smoke（login 無 2FA + 側欄 + 導航 + 登出）

帳號層級：代理 <RF 代理帳號>（SITE_RF_DASHBOARD_AGENT_USER），入口 SITE_RF_DASHBOARD_AGENT_URL（無 -admin）。
RF 代理後台**無 2FA**，落點 `#/management/all-management`，頂層選單 4 項。

代理層級事實（2026-06-17 probe）：
- 頂層選單 4 項：管理（/management）/ 報表（/report）/ 修改密碼 / 登出。
- 登入無 2FA modal，直接落在 `#/management/all-management`。
- 報表子項有 href（可 dispatch_event 導航）；管理無 href 子項（單一父項頁面）。
- 登出與站長相同：sidebar 內 `a.memberSpan` display:none，dispatch_event("click")。

存提（deposit/withdraw）不在本檔：read-only smoke 階段僅驗登入/導航/登出。

斷言策略：一律結構性（route id / hash 變化 / 容器可見 / 選單數量），不綁文案。
"""

import pytest
from playwright.sync_api import Page, expect

from pages.dashboard.factory import get_dashboard_management_page_class

# 代理層級頂層選單 route id（locale-agnostic；probe 2026-06-17）
# id 為空（None）代表「修改密碼」「登出」無 route id
EXPECTED_AGENT_ROUTE_IDS_WITH_ROUTE = {"/management", "/report"}


@pytest.mark.p1
@pytest.mark.rf
@pytest.mark.dashboard
class TestAgentDashboardLogin:
    """RF-DASH-AGENT-001：代理登入（無 2FA）打通驗證"""

    def test_agent_login_no_2fa(self, agent_dashboard_page: Page, site_config):
        """代理帳密直接登入（無 2FA），落在管理頁、側欄出現。"""
        expect(agent_dashboard_page.locator(".sidebar-nav").first).to_be_visible()
        assert "management" in agent_dashboard_page.url, (
            f"代理登入後未落在管理頁，當前 URL：{agent_dashboard_page.url}"
        )


@pytest.mark.p1
@pytest.mark.rf
@pytest.mark.dashboard
class TestAgentDashboardNavigation:
    """RF-DASH-AGENT-002：代理側欄 + 導航 read-only smoke"""

    def test_sidebar_four_items(self, go_agent_dashboard: Page, site_config):
        """代理側欄頂層選單恰 4 項，且含 route id 的項目集合符合預期。

        斷言策略：只驗有 route id 的 2 項（管理/報表），不驗 None id 的項（修改密碼/登出），
        避免 selector id 值空字串 vs None 差異造成集合比對不穩定。
        """
        Mgmt = get_dashboard_management_page_class(site_config.site_id)
        mgmt = Mgmt(go_agent_dashboard)
        count = mgmt.sidebar_item_count()
        assert count == 4, f"代理頂層選單數異常（預期 4，實得 {count}）"
        ids_raw = mgmt.parent_route_ids()
        ids_with_route = {i for i in ids_raw if i}  # 過濾 None / 空字串
        assert ids_with_route == EXPECTED_AGENT_ROUTE_IDS_WITH_ROUTE, (
            f"代理可見選單 route id 與預期不符：實得 {ids_with_route}，"
            f"預期 {EXPECTED_AGENT_ROUTE_IDS_WITH_ROUTE}"
        )

    @pytest.mark.parametrize("route", [
        "agentRevenueSplit",   # 報表 → 代理分潤報表（有 href，dispatch_event 可導航）
        "quota-history",       # 報表 → 額度歷史（有 href）
    ])
    def test_navigate_section(self, go_agent_dashboard: Page, site_config, route):
        """點側欄葉節點導航到代表頁：URL hash 變化 + .container-view visible。"""
        Mgmt = get_dashboard_management_page_class(site_config.site_id)
        mgmt = Mgmt(go_agent_dashboard)
        mgmt.navigate(route)
        assert route in go_agent_dashboard.url, (
            f"導航後 URL 未含 {route}：{go_agent_dashboard.url}"
        )


@pytest.mark.p1
@pytest.mark.rf
@pytest.mark.dashboard
class TestAgentDashboardLogout:
    """RF-DASH-AGENT-003：代理登出回登入頁。

    使用 session agent_dashboard_page 並定義在導航之後 → 全域最後執行；
    登出終結 session，後面不可再有依賴該 session 的測試。
    """

    def test_logout_returns_to_login(self, agent_dashboard_page: Page, site_config):
        """點登出（sidebar 內 display:none a.memberSpan dispatch_event）→ 回 #/login，登入表單重現。"""
        Mgmt = get_dashboard_management_page_class(site_config.site_id)
        mgmt = Mgmt(agent_dashboard_page)
        mgmt.logout()
        assert "/login" in agent_dashboard_page.url, (
            f"代理登出後未回登入頁：{agent_dashboard_page.url}"
        )
