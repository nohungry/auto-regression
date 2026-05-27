"""
RD 語系下拉選單結構驗證 (狗狗娛樂城)
RD-TC-L01

驗證 RD 站 navbar 語言切換下拉選單應包含 5 個語系（無泰語，與 RC/RE 6 語系不同）。

RD 與 RC/RE 不同：navbar 語言觸發是 `button` 顯示當前語言名稱（如「繁體中文」），
非 globe icon。dropdown options 是 `div.cursor-pointer` + 內含 `<p>` 顯示語系名。
"""

import pytest
from playwright.sync_api import Page, expect, TimeoutError as PlaywrightTimeoutError
from utils.dialog_helper import dismiss_server_error_if_present, dismiss_dialog_mask_if_present
from utils.screenshot_helper import get_screenshotter


EXPECTED_LANGUAGES = [
    "繁體中文",
    "簡体中文",
    "English",
    "Tiếng Việt",
    "日本語",
]


@pytest.mark.p1
@pytest.mark.rd
@pytest.mark.language
class TestLanguageDropdown:
    """RD-TC-L01：語系下拉選單結構（5 個語系）"""

    def test_dropdown_has_five_languages(self, page: Page, site_config):
        """RD-TC-L01：navbar 語言下拉選單應有 5 個語系，且每個語系名稱可見"""
        page.goto(site_config.url, wait_until="domcontentloaded")
        dismiss_server_error_if_present(page)
        # 公告蓋板會攔住 navbar 點擊，需先關掉
        dismiss_dialog_mask_if_present(page)
        sh = get_screenshotter(page)

        # 觸發按鈕：navbar 上顯示當前語言的 button（預設「繁體中文」）
        # NOTE: 此按鈕的 click handler 無法被 Playwright `.click()` 觸發（實測 dropdown 不展開），
        # 必須用 `dispatch_event("click")` 直接打 DOM event 才會 toggle dropdown 狀態。
        # SPA hydration race：click handler 在 ~3-4s 後才綁上，dispatch 前需等 hydration 完成。
        lang_trigger = page.locator("button.bg-shade03").filter(has_text="繁體中文").first
        expect(lang_trigger).to_be_visible(timeout=10000)
        lang_trigger.scroll_into_view_if_needed()
        if sh: sh.capture(lang_trigger, "click_語言觸發按鈕")

        first_option = page.locator("div.cursor-pointer p", has_text=EXPECTED_LANGUAGES[0]).first
        # Retry pattern：第一次 dispatch 可能 hydration 未完成；3s 內 dropdown 沒展開則重試一次
        lang_trigger.dispatch_event("click")
        try:
            first_option.wait_for(state="visible", timeout=3000)
        except PlaywrightTimeoutError:
            page.wait_for_timeout(2000)  # 等 hydration 完成
            lang_trigger.dispatch_event("click")
            first_option.wait_for(state="visible", timeout=10000)

        if sh: sh.full_page("verify_語系選單_5個語系")

        # 逐一驗證每個語系名稱在 dropdown 中可見
        for lang_name in EXPECTED_LANGUAGES:
            option = page.locator("div.cursor-pointer p", has_text=lang_name).first
            if sh: sh.capture(option, f"verify_語系_{lang_name}")
            expect(option).to_be_visible()
