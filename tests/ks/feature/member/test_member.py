"""
KS 會員中心功能測試（Super9娛樂城）
KS-MEMBER-001 ~ 003

probe 2026-06-06：KS 右側 drawer 內為 member-center 連結
（/member-center?type=MyAccount / AccountDetails / MemberMessages 等，與 LG 同 scheme）。
驗證點選後 URL 帶對應 type。
"""

import pytest
from playwright.sync_api import Page
from pages.factory import get_home_page_class
from utils.screenshot_helper import get_screenshotter


HomePage = get_home_page_class("ks")


@pytest.mark.p1
@pytest.mark.ks
@pytest.mark.member
class TestMemberCenter:
    """KS-MEMBER-001 ~ 003：會員中心入口導航"""

    @pytest.mark.parametrize(
        "type_key", ["MyAccount", "AccountDetails", "MemberMessages"]
    )
    def test_member_link_navigates(self, class_logged_in_page: Page, go_home, type_key):
        """KS-MEMBER-00x：drawer 點會員中心連結後 URL 帶 type=<key>"""
        page = class_logged_in_page
        home = HomePage(page)
        sh = get_screenshotter(page)

        home.click_member_link(type_key)

        page.wait_for_url(lambda url: f"type={type_key}" in url, timeout=8000)
        assert "/member-center" in page.url, f"預期進 member-center，實際 {page.url}"
        if sh: sh.full_page(f"verify_member_{type_key}")
