"""
RF 會員中心功能測試（金爺娛樂城，信用版）
RF-MEMBER-001 ~ 003

probe 結果（dev-rf，2026-06-17）：
- dropmenu 點「修改資料」或「會員訊息」均開啟同一個帳戶設定 modal
  (div.base-modal.account-settings-modal)。
- modal sidebar 有兩個 tab：修改密碼（index 0）/ 會員訊息（index 1）。
- 個人資訊（帳號）：.account-settings__profile dt/dd
  → dt「會員帳號：」, dd = 帳號名（如 drfauto01）。
- 會員訊息面板：.account-settings-messages__state（無訊息時顯示「目前沒有訊息」）。
- 信用版無存提功能，所有操作均唯讀。

斷言策略：
- 帳號名驗「包含」登入帳號（不寫死完整字串以防未來帳號變更）。
- 訊息狀態文字驗「非空」（目前沒有訊息 / 或有訊息列表可見），不寫死特定訊息內容。
- 每個操作步驟前截圖，assertion 在截圖之後。
"""

import pytest
from playwright.sync_api import Page, expect
from pages.factory import get_home_page_class
from utils.screenshot_helper import get_screenshotter


HomePage = get_home_page_class("rf")


@pytest.mark.p1
@pytest.mark.rf
@pytest.mark.member
class TestMemberCenter:
    """RF-MEMBER-001 ~ 003：帳戶設定 modal 基本驗證"""

    def test_account_settings_modal_opens(self, class_logged_in_page: Page, go_home):
        """RF-MEMBER-001：點「修改資料」能開啟帳戶設定 modal，modal title 為「帳戶設定」。

        斷言策略：modal 容器可見 + title-text 文字 = 帳戶設定（穩定 class selector）。
        唯讀操作，關閉 modal 後狀態還原。
        """
        page = class_logged_in_page
        home = HomePage(page)
        sh = get_screenshotter(page)

        # 前截圖（開 modal 前）
        if sh:
            sh.capture(home.account_box, "verify_帳號區可見_pre_open_modal")

        home.open_account_settings()

        # modal 可見 + title 驗證（截圖在 assert 前）
        title_el = page.locator(".title-text")
        title_el.scroll_into_view_if_needed()
        if sh:
            sh.capture(title_el, "verify_帳戶設定modal_title文字")

        expect(title_el).to_contain_text("帳戶設定", timeout=5000)

        # teardown：關閉 modal 讓下個 test 能操作 loginInBox
        home.close_account_settings()

    def test_account_settings_profile_shows_username(self, class_logged_in_page: Page, go_home, site_config):
        """RF-MEMBER-002：帳戶設定 modal 內的個人資訊顯示登入帳號名。

        斷言策略：
        - .account-settings__profile dd 取帳號值，驗「包含」登入帳號 site_config.username
          （對齊 smoke 的 verify_login_success 策略；用 site_config 取代寫死，可防帳號顯示 regression）。
        """
        page = class_logged_in_page
        home = HomePage(page)
        sh = get_screenshotter(page)

        home.open_account_settings()

        profile_dd = page.locator(".base-modal__container .account-settings__profile dd").first
        profile_dd.scroll_into_view_if_needed()
        if sh:
            sh.capture(profile_dd, "verify_個人資訊帳號非空_pre_assert")

        account_name = home.get_profile_account_name()
        # 驗非空
        assert account_name, f"帳號名稱不應為空，實際: {repr(account_name)}"
        # 驗顯示的帳號名「包含」登入帳號（site_config.username），真正守住帳號顯示 regression
        assert site_config.username.lower() in account_name.lower(), (
            f"個人資訊應顯示登入帳號 {site_config.username}，實際: {repr(account_name)}"
        )

        if sh:
            sh.full_page(f"verify_個人資訊帳號非空_{account_name}")

        home.close_account_settings()

    def test_member_inbox_tab_visible(self, class_logged_in_page: Page, go_home):
        """RF-MEMBER-003：帳戶設定 modal 切換到「會員訊息」tab，訊息狀態文字可見。

        斷言策略：
        - 切換後 .account-settings-messages__state 可見（有內容）。
        - 不寫死訊息文字（「目前沒有訊息」可能隨資料變動）。
        """
        page = class_logged_in_page
        home = HomePage(page)
        sh = get_screenshotter(page)

        home.open_account_settings()

        # 切換到「會員訊息」tab（index=1）
        home.click_member_menu_tab(1)

        # 訊息狀態文字截圖（截圖在 assert 前）
        state_el = page.locator(".account-settings-messages__state")
        if sh:
            sh.capture(state_el, "verify_會員訊息狀態文字_pre_assert")

        inbox_text = home.get_inbox_state_text()
        assert inbox_text, f"會員訊息狀態文字不應為空，實際: {repr(inbox_text)}"

        if sh:
            sh.full_page(f"verify_會員訊息狀態_{inbox_text[:20]}")

        home.close_account_settings()
