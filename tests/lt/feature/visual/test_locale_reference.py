"""
多語系參考截圖（不做比對，供人工審核）

將 5 語系的 login_page / member_menu / betting_record 存檔至
`screenshots/lt/vr_reference/`，供設計與 QA 人工 review。

未來若導入 Docker 做 pixel-level snapshot 比對（方向 4），
會以獨立檔案 + `docker_only` marker 實作，不在此檔中啟用 assertion。
"""

from __future__ import annotations

import os
import pytest
from playwright.sync_api import Page

from pages.lt.login_page import LoginPage
from utils.screenshot_helper import get_screenshotter

from tests.lt.feature.i18n._locale_helpers import (
    LOCALES,
    LOCALE_IDS,
    login_with_locale,
    open_member_menu,
    open_member_screen,
)


_OUT_DIR = "screenshots/lt/vr_reference"

# dev-lt 2026-04-23 i18n hydration regression：non-tw locale 登入後底部 tabbar 會
# 出現 raw i18n key（如 `front.category_icons.*`），導致 `.shadow-menubar` 結構/readiness
# 判斷不穩。守門策略：tw 正常跑、non-tw 以 xfail(strict=True) 守門；產品修復後 XPASS
# 會轉為 FAIL 通知測試端移除標記。見 test_i18n_hydration.py 與 dev-notes。
_NON_TW_XFAIL_REASON = (
    "dev-lt 2026-04-23 i18n hydration regression: non-tw locale 下 `/member-center` "
    "導航受 raw i18n key 影響無法穩定完成；產品修復後應轉 XPASS → 移除此標記。"
)
_LOCALES_XFAIL_NON_TW = [
    pytest.param(loc, label, id=loc) if loc == "tw"
    else pytest.param(
        loc, label, id=loc,
        marks=pytest.mark.xfail(strict=True, reason=_NON_TW_XFAIL_REASON),
    )
    for loc, label in LOCALES
]


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

    @pytest.mark.parametrize("locale,locale_label", _LOCALES_XFAIL_NON_TW)
    def test_member_menu_reference(self, page: Page, site_config, locale, locale_label):
        login_with_locale(page, site_config, locale)
        sh = get_screenshotter(page)
        # 登入後先存一張「登入完成」狀態；若 open_member_menu 失敗仍有 pre-navigation 證據
        if sh: sh.full_page(f"verify_{locale}_登入完成_pre_navigation")
        open_member_menu(page)
        page.wait_for_timeout(1500)
        if sh: sh.full_page(f"verify_{locale}_member_menu_參考截圖")
        _save(page, f"locale-{locale}-member-menu.png")

    @pytest.mark.parametrize("locale,locale_label", _LOCALES_XFAIL_NON_TW)
    def test_betting_record_reference(self, page: Page, site_config, locale, locale_label):
        login_with_locale(page, site_config, locale)
        sh = get_screenshotter(page)
        if sh: sh.full_page(f"verify_{locale}_登入完成_pre_navigation")
        open_member_screen(page, locale, "bettingRecord")
        page.wait_for_timeout(1500)
        if sh: sh.full_page(f"verify_{locale}_betting_record_參考截圖")
        _save(page, f"locale-{locale}-betting-record.png")
