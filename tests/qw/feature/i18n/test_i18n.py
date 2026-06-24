"""
QW i18n 輕量驗證（LM來財娛樂城）
QW-I18N-001 ~ 002

QW 多語系機制（probe 2026-06-24）：
- 語系由 LaiBetLanguage cookie 控制（tw=繁體中文）。
- 沒有可見的語言切換 toggle UI（不同於 KS 的「简体/English」toggle）。
- 前台顯示繁體中文（「最新公告」、「今日不再顯示」、首頁 nav 等均繁中）。
- LaiBetLanguage cookie 自動設定（進站即有，無需手動切換）。

範圍（輕量驗證）：
  I18N-001：LaiBetLanguage cookie 已設定（語系 cookie 存在性）
  I18N-002：cookie 值為已知語系（tw / en / ...），格式合法
  （補充：QW 無可見 toggle，若需驗語言切換行為請由 selector-explorer 探查）
"""

import pytest
from playwright.sync_api import Page
from utils.screenshot_helper import get_screenshotter

VALID_LANG_VALUES = {"tw", "en", "cn", "th", "vn"}


@pytest.mark.p1
@pytest.mark.qw
@pytest.mark.i18n
class TestI18n:
    """QW-I18N-001 ~ 002：LaiBetLanguage cookie 存在性與合法性"""

    def test_lang_cookie_set(self, page: Page, site_config):
        """QW-I18N-001：進首頁後 LaiBetLanguage cookie 已設定

        斷言策略：
        - LaiBetLanguage cookie 存在（非空）
        - 不寫死特定值，驗存在性即可
        （cookie 值依站台設定，預設 tw，但不應綁死 expected value 以免站台改預設語系）
        """
        page.goto(site_config.url, wait_until="domcontentloaded", timeout=60000)
        page.wait_for_timeout(2000)

        sh = get_screenshotter(page)
        if sh: sh.full_page("verify_首頁_for_cookie_check")

        cookies = {c["name"]: c["value"] for c in page.context.cookies()}
        assert cookies.get("LaiBetLanguage"), (
            f"預期 LaiBetLanguage cookie 已設定且非空，"
            f"實際 cookies={list(cookies)}"
        )

    def test_lang_cookie_value_valid(self, page: Page, site_config):
        """QW-I18N-002：LaiBetLanguage cookie 值為已知語系代碼

        斷言策略：
        - cookie 值須在 VALID_LANG_VALUES 集合中（tw/en/cn/th/vn）
        - 確認語系代碼合法，不會出現亂碼或未定義語系
        截圖 label 帶實際 cookie 值供 review，策略為「格式合法性驗證」而非「寫死值比對」
        """
        page.goto(site_config.url, wait_until="domcontentloaded", timeout=60000)
        page.wait_for_timeout(2000)

        sh = get_screenshotter(page)

        cookies = {c["name"]: c["value"] for c in page.context.cookies()}
        lang_val = cookies.get("LaiBetLanguage", "")

        if sh: sh.full_page(f"verify_LaiBetLanguage_cookie_格式合法_{lang_val}")

        assert lang_val in VALID_LANG_VALUES, (
            f"LaiBetLanguage cookie 值應為已知語系代碼 {VALID_LANG_VALUES}，"
            f"實際值為 {lang_val!r}"
        )
