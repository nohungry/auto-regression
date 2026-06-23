"""
RF 後台站長登入測試（read-only smoke）

帳號層級：站長 qatest03（SITE_RF_DASHBOARD_USER），入口 SITE_RF_DASHBOARD_URL（含 -admin）。
RF 後台無 2FA，登入後落點 `#/management/all-management`。

斷言策略：
- 登入成功：URL 含 `management`（落點）、`.sidebar-nav` visible。
- 不驗 username 文案（後台未顯示使用者名稱於固定 DOM）。
"""

import pytest
from playwright.sync_api import Page, expect


@pytest.mark.p1
@pytest.mark.rf
@pytest.mark.dashboard
class TestDashboardLogin:
    """RF-DASH-001：後台站長登入（無 2FA）打通驗證"""

    def test_login_no_2fa(self, dashboard_page: Page, site_config):
        """站長帳密直接登入（無 2FA），落在管理頁、側欄出現。
        dashboard_page fixture 已完成 goto → 帳密 → verify_login_success；
        此處對最終狀態做斷言（落在 #/management/**、側欄出現）。
        """
        assert "management" in dashboard_page.url, (
            f"登入後未導向後台管理頁，當前 URL：{dashboard_page.url}"
        )
        expect(dashboard_page.locator(".sidebar-nav").first).to_be_visible()
