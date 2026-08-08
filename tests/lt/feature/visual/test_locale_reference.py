"""
多語系參考截圖（不做比對，供人工審核）

將 5 語系的 login_page / member_panel / betting_record 存檔至
`screenshots/lt/vr_reference/`，供設計與 QA 人工 review。

2026-05-18 換版：i18n hydration regression 已修復（probe 確認），
原 non-tw xfail 守門條件已解除，5 語系全跑。
"""

from __future__ import annotations

import os
import pytest
from playwright.sync_api import Page

from pages.factory import get_login_page_class
from utils.screenshot_helper import get_screenshotter


LoginPage = get_login_page_class("lt")

from tests.lt.feature.i18n._locale_helpers import (
    LOCALES,
    LOCALE_IDS,
    login_with_locale,
    open_member_menu,
    open_member_screen,
)


_OUT_DIR = "screenshots/lt/vr_reference"


def _save(page: Page, name: str) -> None:
    os.makedirs(_OUT_DIR, exist_ok=True)
    with open(f"{_OUT_DIR}/{name}", "wb") as f:
        f.write(page.screenshot(full_page=True, animations="disabled"))


@pytest.mark.p2
@pytest.mark.lt
@pytest.mark.visual_regression
class TestLocaleReference:
    """5 語系 × 3 場景參考截圖存檔（不比對）"""

    @pytest.mark.parametrize("locale,locale_label", LOCALES, ids=LOCALE_IDS)
    def test_login_page_reference(self, page: Page, site_config, locale, locale_label):
        login = LoginPage(page, site_config.url)
        login.goto_login(locale=locale)
        page.wait_for_timeout(2000)
        sh = get_screenshotter(page)
        if sh: sh.full_page(f"verify_{locale}_登入頁參考截圖")
        _save(page, f"locale-{locale}-login-page.png")

    @pytest.mark.parametrize("locale,locale_label", LOCALES, ids=LOCALE_IDS)
    def test_member_menu_reference(self, page: Page, site_config, locale, locale_label):
        login_with_locale(page, site_config, locale)
        sh = get_screenshotter(page)
        # 登入後先存一張「登入完成」狀態；若 open_member_menu 失敗仍有 pre-navigation 證據
        if sh: sh.full_page(f"verify_{locale}_登入完成_pre_navigation")
        open_member_menu(page)
        page.wait_for_timeout(1500)
        if sh: sh.full_page(f"verify_{locale}_member_panel_參考截圖")
        _save(page, f"locale-{locale}-member-panel.png")

    @pytest.mark.parametrize("locale,locale_label", LOCALES, ids=LOCALE_IDS)
    def test_betting_record_reference(self, page: Page, site_config, locale, locale_label):
        login_with_locale(page, site_config, locale)
        sh = get_screenshotter(page)
        if sh: sh.full_page(f"verify_{locale}_登入完成_pre_navigation")
        open_member_screen(page, locale, "bettingRecord")
        page.wait_for_timeout(1500)
        if sh: sh.full_page(f"verify_{locale}_betting_record_參考截圖")
        _save(page, f"locale-{locale}-betting-record.png")
