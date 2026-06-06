"""
LG 會員中心功能測試（大撈家娛樂城）
LG-MEMBER-001 ~ 003

probe 2026-06-06：LG avatar dropdown 內為 member-center 連結
（/member-center?type=MyAccount / AccountDetails / MemberInbox 等）。
驗證點選後 URL 帶對應 type。

使用 class_logged_in_page + go_home（每個 test 前回首頁清公告）。
"""

import pytest
from playwright.sync_api import Page
from pages.factory import get_home_page_class
from utils.screenshot_helper import get_screenshotter


HomePage = get_home_page_class("lg")


@pytest.mark.p1
@pytest.mark.lg
@pytest.mark.member
class TestMemberCenter:
    """LG-MEMBER-001 ~ 003：會員中心入口導航"""

    @pytest.mark.parametrize("type_key", ["MyAccount", "AccountDetails", "MemberInbox"])
    def test_member_link_navigates(self, class_logged_in_page: Page, go_home, type_key):
        """LG-MEMBER-00x：avatar dropdown 點會員中心連結後 URL 帶 type=<key>"""
        page = class_logged_in_page
        home = HomePage(page)
        sh = get_screenshotter(page)

        home.click_member_link(type_key)

        page.wait_for_url(lambda url: f"type={type_key}" in url, timeout=8000)
        assert "/member-center" in page.url, f"預期進 member-center，實際 {page.url}"
        if sh: sh.full_page(f"verify_member_{type_key}")
