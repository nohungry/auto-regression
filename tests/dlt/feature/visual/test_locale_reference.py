"""
多語系參考截圖（不做比對，供人工審核）

將 5 語系的 login_page / member_menu / betting_record 存檔至
`screenshots/dlt/vr_reference/`，供設計與 QA 人工 review。

未來若導入 Docker 做 pixel-level snapshot 比對（方向 4），
會以獨立檔案 + `docker_only` marker 實作，不在此檔中啟用 assertion。
"""

from __future__ import annotations

import os
import pytest
from playwright.sync_api import Page

from pages.dlt.login_page import LoginPage

from tests.dlt.feature.i18n._locale_helpers import (
    LOCALES,
    LOCALE_IDS,
    login_with_locale,
    open_member_menu,
    open_member_screen,
)


_OUT_DIR = "screenshots/dlt/vr_reference"


def _save(page: Page, name: str) -> None:
    os.makedirs(_OUT_DIR, exist_ok=True)
    with open(f"{_OUT_DIR}/{name}", "wb") as f:
        f.write(page.screenshot(full_page=True, animations="disabled"))


@pytest.mark.p2
@pytest.mark.dlt
@pytest.mark.visual_regression
class TestLocaleReference:
    """5 語系 × 3 場景參考截圖存檔（不比對）"""

    @pytest.mark.parametrize("locale,locale_label", LOCALES, ids=LOCALE_IDS)
    def test_login_page_reference(self, page: Page, site_config, locale, locale_label):
        login = LoginPage(page, site_config.url)
        login.goto_login(locale=locale)
        page.wait_for_timeout(2000)
        _save(page, f"locale-{locale}-login-page.png")

    @pytest.mark.parametrize("locale,locale_label", LOCALES, ids=LOCALE_IDS)
    def test_member_menu_reference(self, page: Page, site_config, locale, locale_label):
        login_with_locale(page, site_config, locale)
        open_member_menu(page)
        page.wait_for_timeout(1500)
        _save(page, f"locale-{locale}-member-menu.png")

    @pytest.mark.parametrize("locale,locale_label", LOCALES, ids=LOCALE_IDS)
    def test_betting_record_reference(self, page: Page, site_config, locale, locale_label):
        login_with_locale(page, site_config, locale)
        open_member_screen(page, locale, "bettingRecord")
        page.wait_for_timeout(1500)
        _save(page, f"locale-{locale}-betting-record.png")
