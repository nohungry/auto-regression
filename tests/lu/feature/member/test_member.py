"""
LU 會員中心功能測試（Dlgbet）
LU-MEMBER-001 ~ 002

probe 2026-06-06：LU 左側 sidebar 的可導航會員連結為 /member?type=X
（MemberMessage 信件 / AllAgent 全民代理）。我的帳戶/存款/提現為 in-panel JS
handler（非 URL 導航），故本檔僅涵蓋 href 連結項。
"""

import pytest
from playwright.sync_api import Page
from pages.factory import get_home_page_class
from utils.screenshot_helper import get_screenshotter


HomePage = get_home_page_class("lu")


@pytest.mark.p1
@pytest.mark.lu
@pytest.mark.member
class TestMemberCenter:
    """LU-MEMBER-001 ~ 002：sidebar 會員連結導航"""

    @pytest.mark.parametrize("type_key", ["MemberMessage", "AllAgent"])
    def test_member_link_navigates(self, class_logged_in_page: Page, go_home, type_key):
        """LU-MEMBER-00x：sidebar 點會員連結後 URL 帶 type=<key>（pathname /member）"""
        page = class_logged_in_page
        home = HomePage(page)
        sh = get_screenshotter(page)

        home.click_member_link(type_key)

        page.wait_for_url(lambda url: f"type={type_key}" in url, timeout=8000)
        assert "/member" in page.url, f"預期進 /member，實際 {page.url}"
        if sh: sh.full_page(f"verify_member_{type_key}")
