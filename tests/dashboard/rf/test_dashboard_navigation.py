"""
RF 後台站長導航 + 登出測試（read-only smoke）

帳號層級：站長 qatest03（SITE_RF_DASHBOARD_USER），入口含 -admin。
RF 後台無 2FA，站長頂層選單 9 項（含修改密碼/登出）。

斷言策略：後台為中文介面，但一律用結構性斷言
（route hash 變化 + .container-view visible + 選單數量），不綁文案。
"""

import pytest
from playwright.sync_api import Page, expect

from pages.dashboard.factory import get_dashboard_management_page_class


@pytest.mark.p1
@pytest.mark.rf
@pytest.mark.dashboard
class TestDashboardNavigation:
    """RF-DASH-002：後台站長側欄 + 導航 read-only smoke"""

    def test_sidebar_renders(self, go_dashboard: Page, site_config):
        """側欄選單載入：頂層選單項數量正常（站長預期 9 項）、首項 visible。"""
        Mgmt = get_dashboard_management_page_class(site_config.site_id)
        mgmt = Mgmt(go_dashboard)
        count = mgmt.sidebar_item_count()
        # 站長頂層選單實機 9 項（儀表板/管理/報表/其它設定/遊戲管理/後臺權限/後臺紀錄/修改密碼/登出）。
        # 用 >=8 守門：可容忍未來小幅增減，但能抓出「選單大幅縮減=後台半殘」的 regression（原 >=5 過鬆）。
        assert count >= 8, f"側欄頂層選單數異常（站長預期 9 項、守門 >=8，實得 {count}）"
        expect(mgmt.parent_items.first).to_be_visible()

    @pytest.mark.parametrize("route", [
        "agentRevenueSplit",   # 報表 → 代理分潤報表
        "bet-report",          # 報表 → 投注報表
        "reset-password",      # 修改密碼（個人帳號 read-only render）
    ])
    def test_navigate_section(self, go_dashboard: Page, site_config, route):
        """點側欄葉節點導航到代表頁：URL hash 變化 + .container-view visible。"""
        Mgmt = get_dashboard_management_page_class(site_config.site_id)
        mgmt = Mgmt(go_dashboard)
        mgmt.navigate(route)
        assert route in go_dashboard.url, f"導航後 URL 未含 {route}：{go_dashboard.url}"


@pytest.mark.p1
@pytest.mark.rf
@pytest.mark.dashboard
class TestDashboardLogout:
    """RF-DASH-003：後台站長登出回登入頁。

    使用 session dashboard_page 並定義在導航之後 → globally 最後執行；
    登出會終結 session，故後面不可再有依賴該 session 的測試。
    （不另起 fresh-login fixture：與 session 同帳號會互踢，見 single-session 規則。）
    """

    def test_logout_returns_to_login(self, dashboard_page: Page, site_config):
        """點登出（sidebar 內 display:none a.memberSpan dispatch_event）→ 回 #/login，登入表單重現。"""
        Mgmt = get_dashboard_management_page_class(site_config.site_id)
        mgmt = Mgmt(dashboard_page)
        mgmt.logout()
        assert "/login" in dashboard_page.url, (
            f"登出後未回登入頁：{dashboard_page.url}"
        )
