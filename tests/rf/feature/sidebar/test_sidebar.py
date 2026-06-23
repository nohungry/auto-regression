"""
RF 使用者選單結構測試（金爺娛樂城）
RF-TC-S01 ~ RF-TC-S03

RF 有兩層 user UI：
1. .user-dropmenu（點 .loginInBox 帳號區展開）：含「修改資訊」「會員訊息」「登出」
2. nav.desktopSideMenu__nav（左側常駐，按登入狀態顯示 7 個 .desktopSideMenu__item）：
   個人資訊/遊戲明細/精彩瞬間/站內信/金爺活動專區/金爺公告/固定維護時間

本檔驗「選單 UI 結構完整性」（開啟 + 預期項目齊全），與 member feature 的
「點連結導航到會員頁」區隔 — 這裡只驗選單本身呈現正確。

probe 2026-06-17：
- .user-dropmenu__item 2 個（修改資訊/會員訊息），登出用 .btn-logout button。
- nav.desktopSideMenu__nav 常駐但 visible=False（scale/opacity 隱藏），故用 attached state。
  desktopSideMenu__item span 文字：個人資訊/遊戲明細/精彩瞬間/站內信/金爺活動專區/金爺公告/固定維護時間（7 個）。
- 注意：開啟 dropmenu 後 modal 不會影響 sidebar 結構讀取。
"""

import pytest
from playwright.sync_api import Page
from pages.factory import get_home_page_class
from utils.screenshot_helper import get_screenshotter


HomePage = get_home_page_class("rf")

# dropmenu 應包含的代表性項目（span 文字 + logout button 文字）
# probe 2026-06-17 確認：item[0]=修改資料, item[1]=會員訊息, logout=登出
EXPECTED_DROPMENU_ITEMS = ["修改資料", "會員訊息", "登出"]

# desktopSideMenu 應包含的代表性項目（span 文字）
EXPECTED_SIDEBAR_ITEMS = [
    "個人資訊",
    "遊戲明細",
    "精彩瞬間",
    "站內信",
    "金爺活動專區",
    "金爺公告",
    "固定維護時間",
]


@pytest.mark.p1
@pytest.mark.rf
class TestSidebar:
    """RF 使用者選單結構（class_logged_in_page + go_home）"""

    def test_user_dropmenu_opens(self, class_logged_in_page: Page, go_home):
        """RF-TC-S01：點帳號區後 .user-dropmenu 正常展開且有內容"""
        page = class_logged_in_page
        home = HomePage(page)
        sh = get_screenshotter(page)

        home.open_user_dropdown()

        dropmenu = page.locator(".user-dropmenu")
        dropmenu.wait_for(state="visible", timeout=8000)
        dropmenu.scroll_into_view_if_needed()
        if sh:
            sh.capture(dropmenu, "verify_dropmenu展開")

        # dropmenu 應有至少 2 個 .user-dropmenu__item + logout
        items = page.locator(".user-dropmenu__item")
        item_count = items.count()
        if sh:
            sh.full_page(f"verify_dropmenu項目_{item_count}個")
        assert item_count >= 2, f"dropmenu 項目過少，疑未正常展開：{item_count}"

    def test_user_dropmenu_items(self, class_logged_in_page: Page, go_home):
        """RF-TC-S02：dropmenu 含預期項目（修改資訊/會員訊息/登出）

        斷言策略：
        - 取 .user-dropmenu__item span 文字 + .btn-logout button 文字
        - 驗每個預期項目都存在於實際項目列表中
        - 不寫死項目順序（展開後 DOM 順序即 UI 順序，但不排除往後調整）
        """
        page = class_logged_in_page
        home = HomePage(page)
        sh = get_screenshotter(page)

        home.open_user_dropdown()
        dropmenu = page.locator(".user-dropmenu")
        dropmenu.wait_for(state="visible", timeout=8000)

        # 取所有 item 文字（span + logout button）
        texts = page.evaluate("""() => {
            const spans = document.querySelectorAll('.user-dropmenu__item span');
            const logout = document.querySelectorAll('.user-dropmenu button.btn-logout');
            const result = Array.from(spans).map(el => el.textContent.trim());
            logout.forEach(el => result.push(el.textContent.trim()));
            return result;
        }""")

        dropmenu.scroll_into_view_if_needed()
        if sh:
            sh.full_page(f"verify_dropmenu項目_{len(texts)}項")

        missing = [label for label in EXPECTED_DROPMENU_ITEMS if label not in texts]
        assert not missing, (
            f"dropmenu 缺少預期項目：{missing}，實際：{texts}"
        )

    def test_desktop_sidebar_items(self, class_logged_in_page: Page, go_home):
        """RF-TC-S03：左側 desktopSideMenu 含預期 7 個功能項目

        斷言策略：
        - 用 JS 讀取 span 文字（nav 本身 visible=False 但 DOM attached，元素 attached 可讀取）
        - 驗 7 個 desktopSideMenu__item 都存在
        - 驗每個預期文字標籤都在項目列表中
        """
        page = class_logged_in_page
        sh = get_screenshotter(page)

        # desktopSideMenu nav 可能 visible=False（scale 動畫），用 JS 直接讀
        sidebar_texts = page.evaluate("""() => {
            const items = document.querySelectorAll('.desktopSideMenu__item span');
            return Array.from(items).map(el => el.textContent.trim());
        }""")

        sidebar_nav = page.locator("nav.desktopSideMenu__nav")
        sidebar_nav.wait_for(state="attached", timeout=8000)

        if sh:
            sh.full_page(f"verify_sidebar左側選單_{len(sidebar_texts)}項")

        assert len(sidebar_texts) == 7, (
            f"desktopSideMenu 應有 7 個項目，實際 {len(sidebar_texts)}：{sidebar_texts}"
        )

        missing = [label for label in EXPECTED_SIDEBAR_ITEMS if label not in sidebar_texts]
        assert not missing, (
            f"sidebar 缺少預期項目：{missing}，實際：{sidebar_texts}"
        )
