"""
LU 後台登入測試（第一波：login + TOTP 2FA 打通）
"""

import pytest
from playwright.sync_api import Page, expect


@pytest.mark.p1
@pytest.mark.lu
@pytest.mark.dashboard
class TestDashboardLogin:
    """LU-DASH-001：後台登入（含 TOTP 2FA）打通驗證"""

    def test_login_with_2fa(self, dashboard_page: Page, site_config):
        """後台帳密 + Google Authenticator TOTP 兩步驟驗證登入成功，落在後台儀表板。"""
        # dashboard_page fixture 已完成 goto → 帳密 → 2FA → verify_login_success；
        # 此處對最終狀態做斷言（落在 #/dashboard/**、側欄出現）。
        assert "/dashboard/" in dashboard_page.url, (
            f"登入後未導向後台儀表板，當前 URL：{dashboard_page.url}"
        )
        expect(dashboard_page.locator(".sidebar-nav").first).to_be_visible()
