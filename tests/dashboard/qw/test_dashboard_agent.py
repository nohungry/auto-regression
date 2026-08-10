"""
QW 後台**代理層級** read-only smoke（login 含 2FA + 側欄 + 導航 + 登出）

⚠️ 帳號層級：本檔以代理 SITE_QW_DASHBOARD_AGENT_USER 登入，入口為**無 -admin** 的
   SITE_QW_DASHBOARD_AGENT_URL。QW 代理後台與 LU 同為 Vue admin 結構，page object
   re-export LU。

代理層級事實（2026-06-23 probe）：
- 登入**需 2FA**（QW 代理特有；LU/LG/KS 代理無），TOTP 由 SITE_QW_DASHBOARD_AGENT_TOTP 提供。
- 落點 `#/member/member-management`，頂層選單 **5 項**。
- 側欄可見、子選單需展開、葉節點無 href → 用 `navigate_agent`。

存提（deposit/withdraw）不在本檔：QW 代理為空帳號（0 會員），無法做對稱 balance 驗證，
待有測資的代理帳號再補。

斷言策略：後台 locale 混雜 → 一律結構性（route id / hash 變化 / 容器可見 / 選單數量），不綁文案。
"""

import pytest
from playwright.sync_api import Page, expect

from pages.dashboard.factory import get_dashboard_management_page_class

# 代理層級頂層選單 route id（locale-agnostic；probe 2026-06-23）
EXPECTED_AGENT_ROUTE_IDS = {
    "/member",
    "/agent",
    "/report",
    "/report-bet-count",
    "/statistical-report",
}


@pytest.mark.p1
@pytest.mark.qw
@pytest.mark.dashboard
class TestAgentDashboardLogin:
    """QW-DASH-AGENT-001：代理登入（含 2FA）打通驗證"""

    def test_agent_login_with_2fa(self, agent_dashboard_page: Page, site_config):
        """代理帳密 + 2FA 登入，落在會員管理頁、側欄出現。"""
        expect(agent_dashboard_page.locator(".sidebar-nav").first).to_be_visible()
        assert "/member" in agent_dashboard_page.url, (
            f"代理登入後未落在會員管理頁，當前 URL：{agent_dashboard_page.url}"
        )


@pytest.mark.p1
@pytest.mark.qw
@pytest.mark.dashboard
class TestAgentDashboardNavigation:
    """QW-DASH-AGENT-002：代理側欄 + 導航 read-only smoke"""

    def test_sidebar_five_items(self, go_agent_dashboard: Page, site_config):
        """代理側欄頂層選單恰 5 項，且 route id 與預期權限集合一致。"""
        Mgmt = get_dashboard_management_page_class(site_config.site_id)
        mgmt = Mgmt(go_agent_dashboard)
        count = mgmt.sidebar_item_count()
        assert count == 5, f"代理頂層選單數異常（預期 5，實得 {count}）"
        ids = set(mgmt.parent_route_ids())
        assert ids == EXPECTED_AGENT_ROUTE_IDS, (
            f"代理可見選單 route id 與預期不符：實得 {ids}，預期 {EXPECTED_AGENT_ROUTE_IDS}"
        )

    @pytest.mark.parametrize("parent_id", ["/member", "/agent"])
    def test_navigate_section(self, go_agent_dashboard: Page, site_config, parent_id):
        """展開父選單 → 點葉節點導航：URL hash 含父項 route + 內容容器可見。"""
        Mgmt = get_dashboard_management_page_class(site_config.site_id)
        mgmt = Mgmt(go_agent_dashboard)
        url = mgmt.navigate_agent(parent_id)
        assert parent_id in url, f"導航後 URL 未含 {parent_id}：{url}"

# 代理登出（*-DASH-AGENT-003）已移至 test_zz_dashboard_logout.py：
# 登出終結 session-scoped 的 agent_dashboard_page，須排在所有依賴該 fixture
# 的測試之後（pytest 依檔名字母序收集）。
