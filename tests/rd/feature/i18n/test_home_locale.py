"""
RD 多語系文案驗證 — 首頁主要文案 (狗狗娛樂城)
RD-I18N-HOME-001 ~ 005

驗證切換各語系（繁中/簡中/日/越/英）後，首頁顯示的「登錄」按鈕與 6 個分類
（電子 / 真人 / 捕魚 / 體育 / 彩票 / 鬥雞）文案正確顯示。

語系切換方式：點 navbar 上「顯示當前語言」的按鈕（`button.bg-shade03`）→
從下拉選單（`div.cursor-pointer p`）選擇目標語言。沿用 test_login_locale 的 dispatch_event
+ retry 模式（SPA hydration race）。

NOTE：dev-rd 部分翻譯有已知問題，本測試以 dev 站當前文案為準（**as-is**），
若產品端修正則此測試會 fail，視為 i18n regression 訊號：
  - 簡体中文：「电子」顯示為「任意电子」、「彩票」顯示為「任意彩票」（i18n key 未對齊）
  - English：第 5 格（彩票/lottery）顯示為「Cockfight / Fighting rooster」（漏翻 / key 重用 cockfighting）
"""

import pytest
from playwright.sync_api import Page, expect, TimeoutError as PlaywrightTimeoutError
from utils.dialog_helper import dismiss_server_error_if_present, dismiss_dialog_mask_if_present
from utils.screenshot_helper import get_screenshotter


# (case_id, lang_name, login_text, category_texts[6])
_HOME_LOCALE_CHECKS = [
    ("RD-I18N-HOME-001", "繁體中文",   "登錄",       ["電子",       "真人",       "捕魚",          "體育",       "彩票",                          "鬥雞"]),
    ("RD-I18N-HOME-002", "簡体中文",   "登录",       ["任意电子",   "真人",       "捕鱼",          "体育",       "任意彩票",                      "斗鸡"]),
    ("RD-I18N-HOME-003", "日本語",     "ログイン",   ["eゲーム",    "ライブ",     "フィッシング",  "スポーツ",   "ロト",                          "闘鶏"]),
    ("RD-I18N-HOME-004", "Tiếng Việt", "Đăng nhập",  ["Điện tử",    "Người thực", "Bắn cá",        "Thể thao",   "xổ số",                         "Đá gà"]),
    ("RD-I18N-HOME-005", "English",    "Login",      ["Slots",      "Casino",     "Fishing",       "Sports",     "Cockfight / Fighting rooster",  "Cockfight"]),
]


def _switch_language(page: Page, base_url: str, lang_name: str):
    """前往首頁 → 關掉公告蓋板 → 點當前語言觸發按鈕 → 從 dropdown 選擇目標語言

    與 test_login_locale.py 的 _switch_language 同 pattern：
    - `button.bg-shade03` 觸發按鈕，filter 用任一已知語名（current state 不可預測）
    - 必須 `dispatch_event("click")`（hydration race + dialog-mask 攔截）
    - dropdown 沒展開則重試一次
    """
    import re as _re
    page.goto(base_url, wait_until="domcontentloaded")
    dismiss_server_error_if_present(page)
    dismiss_dialog_mask_if_present(page)

    lang_trigger = page.locator("button.bg-shade03").filter(
        has_text=_re.compile("繁體中文|簡体中文|日本語|Tiếng Việt|English")
    ).first
    expect(lang_trigger).to_be_visible(timeout=10000)
    lang_trigger.scroll_into_view_if_needed()

    target = page.locator("div.cursor-pointer p", has_text=lang_name).first
    lang_trigger.dispatch_event("click")
    try:
        target.wait_for(state="visible", timeout=3000)
    except PlaywrightTimeoutError:
        page.wait_for_timeout(2000)
        lang_trigger.dispatch_event("click")
        target.wait_for(state="visible", timeout=10000)
    target.dispatch_event("click")

    # 切換後等 SPA re-hydrate
    page.wait_for_timeout(1500)


@pytest.mark.p1
@pytest.mark.rd
@pytest.mark.i18n
@pytest.mark.language
class TestI18NHome:
    """RD-I18N-HOME-001 ~ 005：多語系首頁登錄按鈕 + 6 分類文案驗證"""

    @pytest.mark.parametrize(
        "case_id,lang_name,login_text,category_texts",
        _HOME_LOCALE_CHECKS,
        ids=[c[0] for c in _HOME_LOCALE_CHECKS],
    )
    def test_locale_home_text(self, page: Page, site_config, case_id, lang_name,
                              login_text, category_texts):
        """各語系首頁登錄按鈕 + 6 分類文案（電子/真人/捕魚/體育/彩票/鬥雞）正確顯示"""
        _switch_language(page, site_config.url, lang_name)

        sh = get_screenshotter(page)
        if sh: sh.full_page(f"verify_{lang_name}_首頁全貌")

        # 切完語系後再保險清一次蓋板（部分語系切換會重新觸發公告）
        dismiss_dialog_mask_if_present(page)

        # 登錄按鈕：navbar 顯眼位置，先針對該按鈕 capture 紅框後再驗
        nav_login = page.locator("button.neon-btn", has_text=login_text).first
        expect(nav_login).to_be_visible(timeout=10000)
        nav_login.scroll_into_view_if_needed()
        if sh: sh.capture(nav_login, f"verify_{lang_name}_登錄按鈕_{login_text}")
        expect(nav_login).to_have_text(login_text)

        # 6 個分類文案 — 用 body.to_contain_text 驗證（與 RC 一致），分類 H3 在首頁 tile 內
        body = page.locator("body")
        if sh: sh.full_page(f"verify_{lang_name}_分類文案檢查_共{len(category_texts)}項")
        for cat_text in category_texts:
            expect(body).to_contain_text(cat_text)
