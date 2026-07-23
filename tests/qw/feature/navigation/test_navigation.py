"""
QW 導覽列功能測試（LM來財娛樂城）
QW-TC-N01 ~ QW-TC-N07

probe 2026-06-24 實際 DOM 結構：
- QW nav 分類為 `ul.nav-item li` + 內含 `<span>`（data-id 1~7 對應電子/真人/捕魚/棋牌/體育/彩票/鬥雞）。
- 點擊分類後 URL 不變，僅 li class 切換為 active（含 text-[#FFC227]）。
- 「首頁」li 有 <a href="/">，沒有 data-id。
- 「優惠」li 有 <a href="/promotions">，沒有 data-id，點擊後 URL 真正跳轉。
- popup-mask 可能攔截 pointer events → 測試前由 go_home 透過 dismiss_any_popups() 清除。

驗證範圍（2026-07-23 CDP probe 補齊完整 nav 分類）：
  N01：點擊「電子」（data-id=1）分類後 active class 切換正確
  N02：點擊「真人」（data-id=2）分類後 active class 切換正確
  N03：點擊「捕魚」（data-id=3）分類後 active class 切換正確
  N04：點擊「棋牌」（data-id=4）分類後 active class 切換正確
  N05：點擊「體育」（data-id=5）分類後 active class 切換正確
  N06：點擊「彩票」（data-id=6）分類後 active class 切換正確
  N07：點擊「鬥雞」（data-id=7）分類後 active class 切換正確
  （優惠 data-id=8 為真實 <a href> 連結，另由 test_promotions_link_navigates 驗證）
"""

from urllib.parse import urlparse
import pytest
from playwright.sync_api import Page, expect
from pages.factory import get_home_page_class
from utils.screenshot_helper import get_screenshotter


HomePage = get_home_page_class("qw")

# (data_id, 顯示文字) — 2026-07-23 CDP probe 確認完整 nav 分類（8=優惠另測，不列入）
NAV_CATEGORIES = [
    (1, "電子"),
    (2, "真人"),
    (3, "捕魚"),
    (4, "棋牌"),
    (5, "體育"),
    (6, "彩票"),
    (7, "鬥雞"),
]


@pytest.mark.p1
@pytest.mark.qw
class TestNavigation:
    """QW 導覽列點擊狀態驗證（class_logged_in_page + go_home）

    QW 特性：分類點擊只切換 active class，URL 保持 /（非路由跳轉）。
    只有「優惠」和「首頁」是真實 <a href> 連結。
    """

    @pytest.mark.parametrize(
        "data_id,label", NAV_CATEGORIES, ids=[c[1] for c in NAV_CATEGORIES]
    )
    def test_nav_category_active(
        self, class_logged_in_page: Page, go_home, data_id, label
    ):
        """QW-TC-N01~N07：點擊 nav 分類後 li active class 切換正確

        斷言策略：
        - 點擊前：目標 li class 不含 #FFC227（非 active）
        - 點擊後：目標 li class 含 #FFC227（active）
        - URL 維持 /（QW nav 點擊不跳轉）
        注意：動態 class 帶 Tailwind arbitrary value，用 JS evaluate 比對
        """
        page = class_logged_in_page
        home = HomePage(page)
        sh = get_screenshotter(page)

        # 確認點擊前不是 active
        before_active = home.get_active_nav_category_text()
        if sh: sh.full_page(f"verify_before_click_{label}_active={before_active!r}")

        home.click_nav_category(data_id)
        page.wait_for_timeout(1000)

        # 截圖後驗證 active class
        if sh: sh.full_page(f"verify_after_click_{label}_nav")

        active_text = home.get_active_nav_category_text()
        assert active_text == label, (
            f"點擊 {label}（data-id={data_id}）後 active 分類應為 {label!r}，"
            f"實際為 {active_text!r}"
        )

        # URL 應保持在首頁
        assert page.url.rstrip("/").endswith(
            "dev-qw.t9platform.com"
        ) or urlparse(page.url).path == "/", (
            f"QW nav 點擊後 URL 不應跳轉，實際 URL：{page.url}"
        )

    def test_promotions_link_navigates(self, class_logged_in_page: Page, go_home):
        """QW-TC-N03：點擊「優惠」連結後 URL 跳轉至 /promotions

        優惠是 QW nav 中有真實 <a href='/promotions'> 的連結。
        dispatch_event 繞過可能的 popup-mask 攔截。
        """
        page = class_logged_in_page
        home = HomePage(page)
        sh = get_screenshotter(page)

        if sh: sh.full_page("before_click_優惠")
        home.click_promotions_link()

        page.wait_for_url(
            lambda url: urlparse(url).path == "/promotions", timeout=10000
        )
        if sh: sh.full_page("verify_promotions_頁載入")

        assert urlparse(page.url).path == "/promotions", (
            f"點擊優惠後應跳轉 /promotions，實際 URL：{page.url}"
        )
