"""
LG 遊戲啟動測試（大撈家娛樂城）
LG-TC-G01 ~ LG-TC-G02

probe 2026-06-07：點電子(slots)分類遊戲卡 hover overlay「開始遊戲」→ window.open
新分頁 → /launchLoading → 轉址至第三方 provider launcher（ugsdev gamelauncher，
Slotmill 等），遊戲在 provider iframe 內。

遊戲為真錢 + 外部 provider + 新分頁，故**不做 spin**（與 RE 的 t9 自家 iframe canvas
CDP 滑鼠手法不同、也不安全）；本檔僅驗「launch pipeline 成功」= 新分頁成功轉址
落到外部 provider host。

⚠️ 外部依賴：launch 測試會等待第三方 provider（staging 環境）轉址完成，provider
偶發不穩 → 靠 --reruns 1 容忍（CI 同款）。
"""

import pytest
from playwright.sync_api import Page
from pages.factory import get_home_page_class
from utils.screenshot_helper import get_screenshotter
from utils.game_launch_helper import launch_first_healthy_game, site_base_domain


HomePage = get_home_page_class("lg")


@pytest.mark.p1
@pytest.mark.lg
@pytest.mark.game
class TestGameLaunch:
    """LG 電子分類遊戲卡啟動驗證

    使用 class_logged_in_page + go_home：每個 test 前回首頁並關進站公告蓋板。
    """

    def test_slots_grid_renders(self, class_logged_in_page: Page, go_home):
        """LG-TC-G01：電子(slots)分類頁遊戲卡 grid 正常渲染（數量 > 0）"""
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
        """LG-TC-G02：點遊戲 → 新分頁轉址至外部 provider 且非錯誤頁（launch pipeline 成功）

        LG 第一款即乾淨載入（Slotmill），故通常 1 次即過；retry 為跨站一致設計。
        """
        page = class_logged_in_page
        home = HomePage(page)
        sh = get_screenshotter(page)

        home.open_slots_category()
        idx, url, host = launch_first_healthy_game(home, site_config.url, sh)
        assert host and site_base_domain(site_config.url) not in host, \
            f"遊戲未轉址至外部 provider，停在：{url}"
