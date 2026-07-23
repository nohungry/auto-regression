"""
QW 會員中心功能測試（LM來財娛樂城）
QW-MEMBER-001 ~ QW-MEMBER-002

probe 2026-06-25：QW 會員中心入口透過 avatar-trigger hover dropdown。
- avatar-menu__panel 展開後含多個 .avatar-menu__item（DIV）
- 點「帳戶管理」（第一個 item）→ URL 跳轉至 /member-center?type=MyAccount

probe 2026-07-23（CDP 實機）：avatar panel 其他項也導向 /member-center 帶不同 type query：
- 帳戶明細 → type=AccountDetails
- 投注紀錄 → type=BettingDetails
- 消息中心 → type=MessageCenter
"""

import pytest
from playwright.sync_api import Page
from pages.factory import get_home_page_class
from utils.screenshot_helper import get_screenshotter


HomePage = get_home_page_class("qw")

# (panel item 文字, 預期 URL query) — 2026-07-23 CDP probe 確認
MEMBER_CENTER_TABS = [
    ("帳戶明細", "type=AccountDetails"),
    ("投注紀錄", "type=BettingDetails"),
    ("消息中心", "type=MessageCenter"),
]


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

    @pytest.mark.parametrize(
        "item_text,expected_type",
        MEMBER_CENTER_TABS,
        ids=[t[0] for t in MEMBER_CENTER_TABS],
    )
    def test_member_center_tab_navigates(
        self, class_logged_in_page: Page, go_home, item_text, expected_type
    ):
        """QW-MEMBER-002：avatar panel 各項導向 /member-center 對應 type query

        參數（panel item 文字 → 預期 URL query）：
        - 帳戶明細 → type=AccountDetails
        - 投注紀錄 → type=BettingDetails
        - 消息中心 → type=MessageCenter

        斷言策略：
        - open_user_menu() 展開 panel → 點指定 item（以文字定位）
        - 用 wait_for_function 輪詢 window.location.href 偵測 SPA pushState 後的 /member-center
          （不用 wait_for_url 直等 navigation：Nuxt SPA client-side router 走 History.pushState
          不觸發 navigation request，wait_for_url 會 timeout）
        - 驗 URL 含 /member-center 與對應 type=
        - 截圖帶完整 URL query 供 review

        文案定位風險：panel item 以文字（如「帳戶明細」）定位——QW 為實質單語系站
        （無語系切換 UI，probe 2026-07-22 確認），文字定位風險已評估；若未來 QW 開通
        多語系切換 UI 需改結構化定位（如 data 屬性 / item index）。
        """
        page = class_logged_in_page
        home = HomePage(page)
        sh = get_screenshotter(page)

        # 等 Nuxt 完全 hydrate 後再互動（比照 test_member_page_navigates：go_home networkidle
        # 後 Vue router handler 有時較晚 attach，leading 等待確保 click handler 已綁定）
        page.wait_for_timeout(800)

        if sh: sh.full_page(f"verify_before_open_member_{expected_type}")
        home.open_user_menu()
        home.click_menu_item_by_text(item_text)

        # SPA pushState：輪詢 window.location.href（同 test_member_page_navigates 手法）
        page.wait_for_function(
            "() => window.location.href.includes('/member-center')",
            timeout=12000,
        )
        current_url = page.url
        if sh: sh.full_page(f"verify_member_center_url_{current_url.split('?')[-1]}")
        assert "/member-center" in current_url, (
            f"預期進 /member-center，實際 URL：{current_url}"
        )
        assert expected_type in current_url, (
            f"點「{item_text}」預期 {expected_type} 在 URL，實際 URL：{current_url}"
        )
