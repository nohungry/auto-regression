"""
RD 側邊欄功能測試 (狗狗娛樂城)

驗證 sidebar 上的常用入口：
1. 已登入：遊戲明細 / 公告 sidebar 點擊行為
2. 未登入：點 sidebar「個人資訊」應觸發登入 modal

與 RC 結構差異：
- RC sidebar 用 `.sidebar-item.<class>`（width=0 隱藏節點）
- RD sidebar 用 `div.cursor-pointer`（含 `p.opacity-0.lg:hidden` 內層 P）
- RD sidebar items 各自開啟不同 dialog（與 RC 類似結構）：
  - 個人資訊 → 個人資訊面板（含總資產 / 登出按鈕）
  - 遊戲明細 → 遊戲明細獨立 dialog（投注紀錄表格）
  - 公告 → popup-announcement-mask（與 announcement_popup 同一彈窗）
- 各 dialog 用各自獨有文字當信號（避免 `.first` 命中錯誤元素）
"""

import pytest
from playwright.sync_api import Page, expect
from pages.factory import get_login_page_class
from utils.screenshot_helper import get_screenshotter
from utils.dialog_helper import dismiss_dialog_mask_if_present


LoginPage = get_login_page_class("rd")


def _click_sidebar_item(page: Page, name: str):
    """點 sidebar 指定項目（dispatch_event 繞過 dialog-mask 攔截）

    sidebar items 都帶 `h-[50px]` + `flex-shrink-0` + `cursor-pointer` 組合
    （與外層較大容器的 `cursor-pointer` 區分，避免 has_text 命中父層）。
    """
    item = page.locator(
        "div.h-\\[50px\\].flex-shrink-0.cursor-pointer", has_text=name
    ).first
    item.scroll_into_view_if_needed()
    item.dispatch_event("click")


@pytest.mark.p1
@pytest.mark.rd
class TestSidebarFeatures:
    """RD-SIDEBAR-001 ~ 002：已登入 sidebar 入口"""

    def test_game_details_opens(self, class_logged_in_page: Page, go_home):
        """RD-SIDEBAR-001：點 sidebar「遊戲明細」開啟遊戲明細 dialog（投注紀錄表格）"""
        page = class_logged_in_page
        sh = get_screenshotter(page)

        if sh: sh.full_page("verify_遊戲明細_點擊前")
        _click_sidebar_item(page, "遊戲明細")
        page.wait_for_timeout(1500)
        if sh: sh.full_page("verify_遊戲明細_點擊後")

        # dialog 獨有的表格欄位文字，當「dialog 已開」信號（與 sidebar P 文字「遊戲明細」區分）
        signal = page.locator("text=投注次數").first
        expect(signal).to_be_visible(timeout=5000)
        if sh: sh.capture(signal, "verify_遊戲明細dialog_投注次數欄")

    def test_announcement_opens(self, class_logged_in_page: Page, go_home):
        """RD-SIDEBAR-002：點 sidebar「公告」重新顯示公告彈窗（含「今日不再顯示」）

        RD 公告彈窗用 `.dialog-mask` + `.dialog-container`（與 announcement_popup feature 同 selector），
        非 RC 的 `popup-announcement-mask`。go_home 會 dismiss 既有公告，再點 sidebar 應重新觸發。
        信號：彈窗內「今日不再顯示」文字（公告彈窗獨有）。
        """
        page = class_logged_in_page
        sh = get_screenshotter(page)

        if sh: sh.full_page("verify_公告_點擊前")
        _click_sidebar_item(page, "公告")
        page.wait_for_timeout(1500)

        # 公告彈窗獨有的「今日不再顯示」字串
        signal = page.locator("text=今日不再顯示").first
        expect(signal).to_be_visible(timeout=5000)
        if sh: sh.full_page("verify_公告彈窗開啟")

        # 收尾：關掉公告，避免影響後續 test
        dismiss_dialog_mask_if_present(page)


@pytest.mark.p1
@pytest.mark.rd
@pytest.mark.login
class TestUnauthenticatedSidebar:
    """RD-SIDEBAR-003：未登入點 sidebar 期望觸發登入 modal（**目前 RD 未實作此 UX**）

    RC 站未登入點 sidebar「個人資訊」會自動跳出登入 modal（友善的引導 UX），但
    dev-rd 點擊後完全無反應。視為產品 UX 缺漏 / 待補完，用 xfail(strict=True) 守門：
    - 目前每次跑都 xfail（pytest 視為 PASS，但 reviewer 看得到 expected failure）
    - 若產品端補上此 UX，test 會 XPASS → strict 模式觸發 fail，提醒 maintainer 移除 xfail
    """

    @pytest.mark.xfail(
        strict=True,
        reason="RD 未實作「未登入點 sidebar 自動觸發登入 modal」UX；產品補上後此 xfail 會 XPASS 守門",
    )
    def test_sidebar_triggers_login(self, page: Page, site_config):
        """RD-SIDEBAR-003：未登入時點 sidebar「個人資訊」應跳出登入 modal（**期望實作**）"""
        sh = get_screenshotter(page)
        login = LoginPage(page, site_config.url)
        login.goto()  # 進首頁 + 清掉公告（不登入）

        if sh: sh.full_page("verify_未登入_sidebar點擊前_pre")
        # 點 sidebar 「個人資訊」 — 預期觸發登入 modal
        _click_sidebar_item(page, "個人資訊")
        page.wait_for_timeout(2000)
        if sh: sh.full_page("verify_未登入_sidebar點擊後_pre_assertion")

        # 期望登入 modal 出現（帳號 input visible） — 目前 dev-rd 不會出現
        expect(login.username_input).to_be_visible(timeout=8000)
        if sh: sh.capture(login.username_input, "verify_未登入點sidebar觸發登入modal")
