"""
QW 會員中心功能測試（LM來財娛樂城）
QW-MEMBER-001

probe 2026-06-25：QW 會員中心入口透過 avatar-trigger hover dropdown。
- avatar-menu__panel 展開後含多個 .avatar-menu__item（DIV）
- 點「帳戶管理」（第一個 item）→ URL 跳轉至 /member-center?type=MyAccount
- 無 KS 式的 /member-center?type=AccountDetails 等，QW 用 type=MyAccount

驗證點選後 URL 帶 type=MyAccount。
不驗其他 member-center type（QW 功能路徑不同於 KS，需另行 probe 確認）。
"""

import pytest
from playwright.sync_api import Page
from pages.factory import get_home_page_class
from utils.screenshot_helper import get_screenshotter


HomePage = get_home_page_class("qw")


@pytest.mark.p1
@pytest.mark.qw
@pytest.mark.member
class TestMemberCenter:
    """QW-MEMBER-001：會員中心入口導航"""

    def test_member_page_navigates(self, class_logged_in_page: Page, go_home):
        """QW-MEMBER-001：avatar panel 點「帳戶管理」後 URL 導向 /member-center?type=MyAccount

        斷言策略：
        - 點 avatar panel 第一個 item（帳戶管理）後等待 URL 含 /member-center
        - 驗 URL query 含 type=MyAccount
        - 截圖帶完整 URL 路徑供 review
        """
        page = class_logged_in_page
        home = HomePage(page)
        sh = get_screenshotter(page)

        # 等 Nuxt 完全 hydrate 後再做互動（整合跑時 go_home networkidle 後 Vue router
        # handler 有時比預期晚 attach，leading 等待確保 click handler 已綁定）
        page.wait_for_timeout(800)

        if sh: sh.full_page("verify_before_open_member")
        home.open_member_page()

        # Nuxt SPA client-side router 跳轉（History.pushState）
        # page.wait_for_url() 底層等 expect_navigation，SPA pushState 不觸發 navigation request
        # → 改用 wait_for_function 輪詢 window.location.href（直接偵測 URL 字串變更）
        page.wait_for_function(
            "() => window.location.href.includes('/member-center')",
            timeout=12000,
        )
        current_url = page.url
        if sh: sh.full_page(f"verify_member_center_url_{current_url.split('?')[-1]}")
        assert "/member-center" in current_url, (
            f"預期進 /member-center，實際 URL：{current_url}"
        )
        assert "type=MyAccount" in current_url, (
            f"預期 type=MyAccount 在 URL，實際 URL：{current_url}"
        )
