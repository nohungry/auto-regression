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

另含 **2FA 登入頻率節流**（`_throttle_2fa_login`，D-026）：帶 TOTP 的登入之間強制
>= 35s 間隔，避免觸發後端 2FA 頻率風控（docs/dashboard-technical-notes.md 規則 2b）。
"""

import time

from pages.dashboard.factory import get_dashboard_login_page_class
from utils.screenshot_helper import (
    ScreenshotHelper,
    attach_screenshotter,
    detach_screenshotter,
)

# 兩次 2FA 登入之間的最小間隔（秒）。
# docs/dashboard-technical-notes.md 規則 2b 要求「連續兩次登入間隔 > 30s」；35s = 該
# 下限 + 裕度。>30s 同時保證跨過一個 TOTP 旋轉窗口，故第二次登入不會拿到與前一次
# 相同的碼（同碼重放後端必拒）。
TWOFA_LOGIN_MIN_INTERVAL_S = 35.0

# 上一次 2FA 登入（嘗試）的時間戳，`time.monotonic()`（不受系統時間校正影響）。
# **刻意不持久化到磁碟**：跨 process 的節流狀態需要 lock / 檔案清理 / 陳舊值失效等
# 機制，複雜度遠高於收益；且 CI 各站分開 job、本機遵守 D-011 同帳號不並行，單一
# pytest session 內節流即可覆蓋實際的連續登入場景。跨 session 的頻率節制仍靠
# 規則 2b 的人為紀律（疑似鎖定就停手冷卻 20-30 分鐘）。
_last_2fa_login_at = None


def _throttle_2fa_login():
    """確保與上一次 2FA 登入相隔 >= TWOFA_LOGIN_MIN_INTERVAL_S，不足則補等。

    **D-006（禁裸 time.sleep）的核可例外**，援引該決策「僅 LU 因真守衛硬等 + 2FA
    風險刻意保留」既有的框架（docs/decisions.md D-006 影響欄）：後端 2FA 頻率風控
    是純 wall-clock 條件 —— 沒有任何 UI 元素、API 回應或 DOM 狀態可以 poll 出
    「現在再登入不會被鎖」，可判定等待在此無從建立。詳見 D-026。

    時間戳在**檢查點**就更新（而非登入成功後），使失敗的 attempt 也計入間隔 ——
    被拒的登入同樣會累積後端的頻率計數，正是最需要節流的情況。
    """
    global _last_2fa_login_at

    now = time.monotonic()
    if _last_2fa_login_at is not None:
        elapsed = now - _last_2fa_login_at
        wait = TWOFA_LOGIN_MIN_INTERVAL_S - elapsed
        if wait > 0:
            print(
                f"[2FA throttle] 距上次 2FA 登入僅 {elapsed:.1f}s，"
                f"等待 {wait:.1f}s 以滿足 >{TWOFA_LOGIN_MIN_INTERVAL_S}s 間隔（規則 2b）",
                flush=True,
            )
            time.sleep(wait)
            now = time.monotonic()
    _last_2fa_login_at = now

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


# LU 型（現金版 Vue admin）側欄葉節點無 href / id / class（Vue @click 程式化導航），
# 唯一穩定識別是顯示文字（後台固定英文 + 未翻譯 i18n key，非多語系切換）→
# 文字版 dump：排除父項錨點（a.memberSpan / 有 id 者），只收葉節點文字。
_MENU_TREE_TEXTS_JS = """
() => {
  const parents = [];
  document.querySelectorAll('.sidebar-nav li.parent-li').forEach(li => {
    const span = li.querySelector('a.memberSpan');
    const leaves = [];
    li.querySelectorAll('li a').forEach(a => {
      if (a.classList.contains('memberSpan') || a.id) return;
      const text = (a.textContent || '').trim().replace(/\\s+/g, ' ');
      if (text) leaves.push(text);
    });
    parents.push([span ? (span.id || '') : '', leaves]);
  });
  return parents;
}
"""


def sidebar_menu_tree_texts(page, timeout: int = 15000):
    """回傳側欄選單樹（文字版）：[(parent_route_id, [子入口顯示文字, ...]), ...]。

    LU 型現金版後台專用：葉節點無 href/id/class（Vue @click），展開與否 DOM
    皆存在但無結構性識別 → 子入口以顯示文字識別（後台為固定英文顯示，
    非多語系切換場景；若產品端翻譯 i18n key 造成文字變動，屬入口檢測要
    回報的變更訊號）。頂層入口仍用父項 route id（結構性）。
    """
    page.locator(".sidebar-nav").first.wait_for(state="attached", timeout=timeout)
    page.locator(".sidebar-nav li.parent-li li a").first.wait_for(
        state="attached", timeout=timeout
    )
    tree = page.evaluate(_MENU_TREE_TEXTS_JS)
    return [(parent_id, texts) for parent_id, texts in tree]


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
    # 2FA 登入頻率節流（規則 2b / D-026）：只有真的帶了 TOTP secret 的登入才 gate。
    # 條件本身不硬編站點清單（新站零維護）——今日實際命中的是現金版的 5 個登入：
    # LG 站長、LU 站長 + 代理、QW 站長 + 代理；信用版 rc/re/lt/rd 傳空字串、rf 走
    # _OMIT 兩引數路徑，皆不進 gate，行為零改變。
    # 放在建 context **之前**：等待期間不佔著瀏覽器 context 與 CDP 連線。
    if totp is not _OMIT and totp:
        _throttle_2fa_login()

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
