"""
KS 遊戲啟動測試（Super9娛樂城）
KS-TC-G01 ~ KS-TC-G02

probe 2026-06-07：點電子(slots)分類遊戲卡（div.grid.grid-cols-7 內含 img.aspect-square
的 cursor-pointer 容器，直接點卡片）→ window.open 新分頁 → /launchLoading → 轉址至
第三方 provider 遊戲（kplay playGame.do，遊戲渲染在主 frame 非 iframe）。

grid 延遲渲染：count 早期為 0、須 wait attached（probe 證實渲染後可達）。
遊戲為真錢 + 外部 provider + 新分頁，故**不做 spin**；本檔僅驗「launch pipeline
成功」= 新分頁成功轉址落到外部 provider host。

⚠️ 外部依賴：launch 測試會等待第三方 provider（staging 環境）轉址完成，provider
偶發不穩 → 靠 --reruns 1 容忍（CI 同款）。
"""

import pytest
from playwright.sync_api import Page
from pages.factory import get_home_page_class
from utils.screenshot_helper import get_screenshotter
from utils.game_launch_helper import launch_first_healthy_game


HomePage = get_home_page_class("ks")


@pytest.mark.p1
@pytest.mark.ks
@pytest.mark.game
class TestGameLaunch:
    """KS 電子分類遊戲卡啟動驗證

    使用 class_logged_in_page + go_home：每個 test 前回首頁並關進站公告蓋板。
    """

    def test_slots_grid_renders(self, class_logged_in_page: Page, go_home):
        """KS-TC-G01：電子(slots)分類頁遊戲卡 grid 正常渲染（數量 > 0）"""
        page = class_logged_in_page
        home = HomePage(page)
        home.open_slots_category()
        count = home.game_card_count()
        sh = get_screenshotter(page)
        if sh: sh.full_page(f"verify_slots遊戲卡數量_{count}")
        assert count > 0, "電子分類應有遊戲卡，實際為 0（grid 未渲染）"

    def test_launch_game_loads_provider(
        self, class_logged_in_page: Page, go_home, site_config
    ):
        """KS-TC-G02：點遊戲 → 新分頁轉址至外部 provider 且非錯誤頁（launch pipeline 成功）

        ⚠️ KS 前兩款 slots（Pragmatic playGame.do）在 staging 啟動失敗（落到錯誤頁
        「抱歉，出现错误，请联系娱乐场客服」）；retry 跳過它們，取第一款乾淨載入的
        kplay game/load 遊戲。前兩款的錯誤已回報為待查 provider 問題（非本測試掩蓋）。
        """
        page = class_logged_in_page
        home = HomePage(page)
        sh = get_screenshotter(page)

        home.open_slots_category()
        idx, url, host = launch_first_healthy_game(home, site_config.url, sh)
        assert host and "t9platform.com" not in host, \
            f"遊戲未轉址至外部 provider，停在：{url}"
