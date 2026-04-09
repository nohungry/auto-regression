"""
多語系版面健康度測試（環境無關）

策略：
- 方向 1：DOM overflow 偵測（scrollWidth > clientWidth 等）
- 方向 5：DOM fingerprint baseline 比對（tag / class / text / font，不含座標）

與舊版 test_locale_visual_matrix 的差異：
- 完全不做 pixel-level 比對 → 跨螢幕/環境穩定
- baseline 為 JSON 而非 PNG → 可 review diff，不需 Docker
- 未來 pixel 比對將以 marker `docker_only` 的獨立檔案處理（方向 4）

5 語系 × 6 場景 = 30 tests
"""

from __future__ import annotations

import pytest
from pathlib import Path
from playwright.sync_api import Page

from pages.dlt.login_page import LoginPage
from utils.layout_fingerprint import assert_fingerprint

from ._locale_helpers import (
    LOCALES,
    LOCALE_IDS,
    assert_no_overflow,
    login_with_locale,
    open_member_menu,
    open_member_screen,
)


_FP_DIR = Path(__file__).parent.parent.parent / "__fingerprints__"


def _fp_path(locale: str, scene: str) -> str:
    return str(_FP_DIR / f"locale-{locale}-{scene}.json")


@pytest.mark.p2
@pytest.mark.dlt
@pytest.mark.locale_layout
class TestLocaleLayout:
    """5 語系 × 6 場景：overflow + DOM fingerprint 驗證（環境無關）"""

    @pytest.mark.parametrize("locale,locale_label", LOCALES, ids=LOCALE_IDS)
    def test_home_shell(self, page: Page, site_config, locale, locale_label):
        login = LoginPage(page, site_config.url)
        login.goto(locale=locale)
        page.wait_for_timeout(3000)
        assert_no_overflow(page, f"{locale_label}首頁")
        assert_fingerprint(page, _fp_path(locale, "home-shell"))

    @pytest.mark.parametrize("locale,locale_label", LOCALES, ids=LOCALE_IDS)
    def test_login_page(self, page: Page, site_config, locale, locale_label):
        login = LoginPage(page, site_config.url)
        login.goto_login(locale=locale)
        page.wait_for_timeout(2000)
        assert_no_overflow(page, f"{locale_label}登入頁")
        assert_fingerprint(page, _fp_path(locale, "login-page"))

    @pytest.mark.parametrize("locale,locale_label", LOCALES, ids=LOCALE_IDS)
    def test_member_menu(self, page: Page, site_config, locale, locale_label):
        login_with_locale(page, site_config, locale)
        open_member_menu(page)
        page.wait_for_timeout(1500)
        assert_no_overflow(page, f"{locale_label}會員側欄")
        assert_fingerprint(page, _fp_path(locale, "member-menu"))

    @pytest.mark.parametrize("locale,locale_label", LOCALES, ids=LOCALE_IDS)
    def test_betting_record(self, page: Page, site_config, locale, locale_label):
        login_with_locale(page, site_config, locale)
        open_member_screen(page, locale, "bettingRecord")
        page.wait_for_timeout(1500)
        assert_no_overflow(page, f"{locale_label}投注紀錄頁")
        assert_fingerprint(page, _fp_path(locale, "betting-record"))

    @pytest.mark.parametrize("locale,locale_label", LOCALES, ids=LOCALE_IDS)
    def test_member_info(self, page: Page, site_config, locale, locale_label):
        login_with_locale(page, site_config, locale)
        open_member_screen(page, locale, "memberInfo")
        page.wait_for_timeout(1500)
        assert_no_overflow(page, f"{locale_label}會員資料頁")
        assert_fingerprint(page, _fp_path(locale, "member-info"))

    @pytest.mark.parametrize("locale,locale_label", LOCALES, ids=LOCALE_IDS)
    def test_maintenance(self, page: Page, site_config, locale, locale_label):
        login_with_locale(page, site_config, locale)
        open_member_screen(page, locale, "maintenance")
        page.wait_for_timeout(1500)
        assert_no_overflow(page, f"{locale_label}維護時間頁")
        assert_fingerprint(page, _fp_path(locale, "maintenance"))
