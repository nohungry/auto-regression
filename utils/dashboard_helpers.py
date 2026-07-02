"""
後台 dashboard 登入 fixture 的共用邏輯。

各站 tests/dashboard/<id>/conftest.py 的 login fixture（dashboard_page /
master_dashboard_page / agent_dashboard_page / fresh_dashboard_page）原本各自
inline 一份「建 context + CDP 最大化 + factory 登入（+可選 screenshotter）+ yield/
close」。這裡把它抽成 generator，fixture body 用 `yield from dashboard_login_session(...)`。

**fixture 仍 per-site 定義（重要）**：session-scoped fixture 若抽到共用父 conftest，
pytest 對單一 FixtureDef 整 session 只快取一次 → 多站同 session 跑會拿到第一站的
登入態（跨站帳號錯亂）。故只抽「邏輯」成本函式，fixture 各站各自定義（獨立快取）。
（同 utils/api_helpers.py 的教訓。）

context 建立複用根 conftest `_new_configured_page(install_toast_observer=False)`：
與前台一致的 CI viewport / 本機 CDP maximize 分支，且**不注入** toast observer
（後台不需要，且避免誤關後台彈窗）。
"""

from conftest import _new_configured_page
from pages.dashboard.factory import get_dashboard_login_page_class
from utils.screenshot_helper import (
    ScreenshotHelper,
    attach_screenshotter,
    detach_screenshotter,
)

# totp 參數的「未提供」哨兵：區分「傳 None/空字串當第三引數」與「完全不傳第三引數」。
# rf 的 DashboardLoginPage.goto_and_login 只吃 (user, pass)；信用版/現金版 2FA 站吃
# (user, pass, totp)。省略時走兩引數呼叫。
_OMIT = object()


def dashboard_login_session(
    browser,
    site_config,
    login_url,
    username,
    password,
    totp=_OMIT,
    screenshot=None,
):
    """Generator：建 context+page → dashboard factory 登入 → yield page → 關 context。

    fixture 用法：`yield from dashboard_login_session(browser, site_config, ...)`。

    totp:
      - 省略（_OMIT）→ 呼叫 goto_and_login(user, pass)（rf 站）。
      - 傳值（含 None/空字串）→ goto_and_login(user, pass, totp)（條件式 2FA 站）。
    screenshot:
      - (label, desc) tuple → 登入流程掛 ScreenshotHelper 逐步截圖（現金版 + rf）。
      - None → 不截（信用版 rc/re/lt/rd）。
    """
    context, page = _new_configured_page(browser, install_toast_observer=False)

    def _login():
        LoginCls = get_dashboard_login_page_class(site_config.site_id)
        login = LoginCls(page, login_url)
        if totp is _OMIT:
            login.goto_and_login(username, password)
        else:
            login.goto_and_login(username, password, totp)

    if screenshot:
        label, desc = screenshot
        sh = ScreenshotHelper(
            page, label, desc, site_id=site_config.site_id, category="feature"
        )
        attach_screenshotter(page, sh)
        try:
            _login()
            sh.generate_report()
        finally:
            detach_screenshotter(page)
    else:
        _login()

    try:
        yield page
    finally:
        context.close()
