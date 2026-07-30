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

from pages.dashboard.factory import get_dashboard_login_page_class
from utils.screenshot_helper import (
    ScreenshotHelper,
    attach_screenshotter,
    detach_screenshotter,
)

# 側欄選單樹 dump（入口檢測用）：一次 evaluate 取回整棵樹，避免逐項 locator round-trip。
# 結構假設（信用版 rc/re/lt/rd/rf 全家 + LU 型站長側欄皆適用，2026-07-30 實機 probe）：
#   .sidebar-nav li.parent-li            — 頂層入口
#   li.parent-li a.memberSpan[id]        — 父項 route id（'' = 非路由項目，如修改密碼/登出）
#   li.parent-li li a[href]              — 子入口（信用版 collapsed DOM 即有 href，毋須展開）
_MENU_TREE_JS = """
() => {
  const parents = [];
  document.querySelectorAll('.sidebar-nav li.parent-li').forEach(li => {
    const span = li.querySelector('a.memberSpan');
    const hrefs = [];
    li.querySelectorAll('li a').forEach(a => {
      const href = a.getAttribute('href') || '';
      if (href) hrefs.push(href);
    });
    parents.push([span ? (span.id || '') : '', hrefs]);
  });
  return parents;
}
"""


def sidebar_menu_tree(page, timeout: int = 15000):
    """回傳側欄選單樹：[(parent_route_id, [子入口 href, ...]), ...]（依側欄順序）。

    入口檢測（menu entry detection）用：與 per-site 預期 spec 精確比對，
    選單增刪、順序、權限變動都會反映在回傳值。識別一律結構性
    （route id / href），不綁文案（後台 locale 混雜）。

    等待策略：側欄 attached 後再等第一個 route href 出現（Vue 選單 href
    為非同步掛載，過早 dump 會拿到空 href）。
    """
    page.locator(".sidebar-nav").first.wait_for(state="attached", timeout=timeout)
    page.locator(".sidebar-nav a[href*='#/']").first.wait_for(
        state="attached", timeout=timeout
    )
    tree = page.evaluate(_MENU_TREE_JS)
    return [(parent_id, hrefs) for parent_id, hrefs in tree]


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
    # lazy import：本模組被 pages/ 層 POM import（sidebar_menu_tree），
    # 頂層 import conftest 會把 pages 層耦合到 pytest 環境 → 延到呼叫時才 import
    from conftest import _new_configured_page

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
