"""
RF 遊戲啟動測試（金爺娛樂城）
RF-TC-G01 ~ RF-TC-G02

probe 2026-06-17：點電子(slots)分類遊戲卡（.gameShowcaseSection__card）→
同頁路由至 /Game?gamePlatformId=...&gameId=...（不開新分頁）→ 頁面有 iframe.game-iframe。
dev 環境 iframe.src 為空（staging provider 未連線），故不等待 iframe 外部 provider 轉址。

本檔驗「遊戲啟動 pipeline」= 分類頁有遊戲卡 + 點擊後 URL 路由至 /Game（同頁路由成功）。
不做 spin、不等 iframe 真正載入（唯讀，不下注，不依賴外部 provider 穩定性）。

RF 遊戲行為與 LG/LU/KS 不同：不開新分頁，故不用 context.expect_page()，
用 page.wait_for_url(lambda url: '/Game' in url) 驗同頁路由。
"""

import pytest
from playwright.sync_api import Page
from pages.factory import get_home_page_class
from utils.screenshot_helper import get_screenshotter


HomePage = get_home_page_class("rf")


@pytest.mark.p1
@pytest.mark.rf
@pytest.mark.game
class TestGameLaunch:
    """RF 電子分類遊戲卡啟動驗證

    使用 class_logged_in_page + go_home：每個 test 前回首頁並清理 base-modal 彈窗。
    """

    def test_slots_grid_renders(self, class_logged_in_page: Page, go_home):
        """RF-TC-G01：電子(slots)分類頁遊戲卡 grid 正常渲染（數量 > 0）

        斷言策略：
        - 導航至 /Categories/slots 後，驗 .gameShowcaseSection__card count > 0
        - 只驗「有資料」，不寫死特定數量（動態）
        """
        page = class_logged_in_page
        home = HomePage(page)

        home.open_slots_category()
        count = home.game_card_count()

        sh = get_screenshotter(page)
        if sh:
            sh.full_page(f"verify_slots遊戲卡數量_{count}")
        assert count > 0, f"電子分類應有遊戲卡，實際為 0（grid 未渲染）"

    def test_launch_game_routes_to_game_page(
        self, class_logged_in_page: Page, go_home
    ):
        """RF-TC-G02：點遊戲卡 → 同頁路由至 /Game?... 且 game-iframe 存在（launch pipeline 成功）

        斷言策略：
        - 驗 URL 已包含 /Game（同頁路由已觸發）
        - 驗 iframe.game-iframe 存在（遊戲容器已渲染）
        - 不等 iframe.src 載入外部 provider（dev 環境 staging provider 可能未連線）

        RF 與 LG/LU/KS 差異：RF 點遊戲不開新分頁，是 Nuxt router push 同頁切換。
        """
        page = class_logged_in_page
        home = HomePage(page)
        sh = get_screenshotter(page)

        home.open_slots_category()

        if sh:
            sh.full_page("verify_slots分類頁遊戲卡pre_click")

        final_url = home.launch_game(index=0)

        if sh:
            sh.full_page(f"verify_遊戲頁路由完成_{final_url.split('?')[0].split('/')[-1]}")

        # 驗 URL 包含 /Game（同頁路由成功）
        assert "/Game" in final_url, (
            f"點遊戲卡後 URL 應含 /Game，實際：{final_url}"
        )

        # 驗 game-iframe 容器存在（遊戲頁 DOM 結構正確）
        game_iframe = page.locator("iframe.game-iframe")
        game_iframe.wait_for(state="attached", timeout=10000)
        count = game_iframe.count()
        if sh:
            sh.full_page(f"verify_game_iframe_count_{count}")
        assert count == 1, (
            f"遊戲頁應有 1 個 iframe.game-iframe，實際 {count}"
        )
