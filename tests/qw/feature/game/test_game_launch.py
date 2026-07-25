"""
QW 遊戲功能測試（LM來財娛樂城）
QW-TC-G01 ~ QW-TC-G03

probe 2026-06-25：QW 遊戲入口路徑（與 KS/LU 不同）：
  首頁 .intro-tab 分類 tab（6 個：電子/真人/捕魚/棋牌/體育/彩票，active 用 .intro-tab--active）
    + .intro-platform.group provider tiles（DIV，Vue handler click，無 href）
  → 點 intro-platform → Nuxt SPA 路由 → /Categories/slots?gamePlatformId=XXX（電子）
  → 頁面出現 div.grid.grid-cols-8，遊戲卡為 div.group.relative.h-[124px].w-[124px].cursor-pointer
  → 點遊戲卡 → window.open 新分頁 → /launchLoading

⚠️ Game Launch 狀態（probe 2026-06-25）：
  新分頁開啟後 3 秒仍停在 /launchLoading，未轉址至第三方 provider。
  body 為空（launchLoading 後端 token 無法取得或 provider 配置未完成）。
  這是 **provider/後端配置問題**（第三方遊戲後端壞），非網站自身流程問題。
  比照 RC/RE/RD 處理：game launch 測試加 @pytest.mark.skip + 完整說明理由。

移除 skip 時機：dev 環境 provider 配置完成，/launchLoading 可正常轉址至 provider host。
"""

import pytest
from playwright.sync_api import Page, expect
from pages.factory import get_home_page_class
from utils.screenshot_helper import get_screenshotter


HomePage = get_home_page_class("qw")


@pytest.mark.p1
@pytest.mark.qw
@pytest.mark.game
class TestGameLaunch:
    """QW 遊戲列表與啟動驗證

    使用 class_logged_in_page + go_home：每個 test 前回首頁並清進站公告彈窗。

    QW 遊戲架構：
    - 首頁 intro-tab 分類 → intro-platform provider tiles → 點 tile → 分類頁
    - 分類頁（/Categories/slots?gamePlatformId=XXX）→ 遊戲 grid
    - 點遊戲卡 → 新分頁 /launchLoading → 轉址 provider（dev 環境未完成）
    """

    def test_intro_tabs_visible(self, class_logged_in_page: Page, go_home):
        """QW-TC-G01：首頁遊戲 intro-tab 分類可見（6 個：電子/真人/捕魚/棋牌/體育/彩票）

        斷言策略：
        - .intro-tab 元素數量 == 6
        - 第一個 tab 含 .intro-tab--active（首頁預設電子分類 active）
        - 至少一個 .intro-platform 可見（provider tiles 渲染正常）
        不驗文案（多語系站）。
        """
        page = class_logged_in_page
        sh = get_screenshotter(page)

        # 滾動到 intro 區
        intro = page.locator(".intro-tab").first
        intro.scroll_into_view_if_needed()
        page.wait_for_timeout(500)

        tab_count = page.locator(".intro-tab").count()
        if sh: sh.capture(intro, f"verify_intro_tab_count_{tab_count}")
        if sh: sh.full_page(f"verify_intro_section_tab{tab_count}")

        assert tab_count == 6, (
            f"首頁 intro-tab 應有 6 個分類，實際：{tab_count}"
        )

        # 驗 intro-platform 數量（provider tiles）
        plat_count = page.locator(".intro-platform").count()
        first_platform = page.locator(".intro-platform").first
        first_platform.scroll_into_view_if_needed()
        if sh: sh.capture(first_platform, f"verify_intro_platform_count_{plat_count}")

        assert plat_count > 0, (
            f"首頁 intro-platform provider tiles 不應為 0，實際：{plat_count}"
        )

    def test_slots_category_page_renders(self, class_logged_in_page: Page, go_home):
        """QW-TC-G02：點電子分類 intro-platform → URL 跳轉且遊戲 grid 渲染（count > 0）

        斷言策略：
        - 點第一個 .intro-platform（電子分類 provider tile）
        - URL 跳轉至 /Categories/slots?gamePlatformId=XXX（Nuxt SPA pushState）
        - 遊戲卡 grid 渲染，count > 0（驗渲染健康度）
        不點遊戲卡（launch 流程有 skip，見 QW-TC-G03）。
        """
        page = class_logged_in_page
        home = HomePage(page)
        sh = get_screenshotter(page)

        page.wait_for_timeout(800)
        if sh: sh.full_page("before_click_intro_platform")

        home.open_slots_category()

        # 等 Nuxt SPA 路由跳轉（/Categories/slots）
        page.wait_for_function(
            "() => window.location.href.includes('/Categories/slots')",
            timeout=12000,
        )
        current_url = page.url
        if sh: sh.full_page(f"verify_slots_url_{current_url.split('?')[-1]}")

        assert "/Categories/slots" in current_url, (
            f"預期 URL 含 /Categories/slots，實際：{current_url}"
        )

        # 等待遊戲 grid 渲染
        game_card = page.locator(HomePage.GAME_CARD)
        game_card.first.wait_for(state="attached", timeout=20000)
        count = home.game_card_count()

        if sh: sh.full_page(f"verify_game_card_count_{count}")

        assert count > 0, (
            f"電子分類頁遊戲卡應 > 0，實際：{count}（grid 未渲染）"
        )

    @pytest.mark.skip(
        reason=(
            "QW-TC-G03 SKIP：dev 環境 game launch 後端未配置完成。"
            "probe 2026-06-25：點遊戲卡 → 新分頁開啟 → 停在 /launchLoading（3 秒後仍未轉址）。"
            "launchLoading 後端無法取得 provider token 並轉址至第三方 provider host（body 空白）。"
            "這是 provider/後端配置問題，非本站 UI 流程問題（屬第三方遊戲後端問題，可接受 skip）。"
            "移除 skip 時機：dev 環境 provider 申請完成，/launchLoading 可正常轉址。"
        )
    )
    def test_launch_game_loads_provider(
        self, class_logged_in_page: Page, go_home, site_config
    ):
        """QW-TC-G03：點遊戲 → 新分頁轉址至外部 provider（dev 環境 launch 後端未就緒，SKIP）

        此 test 在 dev 環境固定 skip（launchLoading 不轉址）。
        flow 設計保留如下，供未來環境就緒時直接啟用。
        """
        page = class_logged_in_page
        home = HomePage(page)
        sh = get_screenshotter(page)

        home.open_slots_category()
        page.wait_for_function(
            "() => window.location.href.includes('/Categories/slots')",
            timeout=12000,
        )

        # 等遊戲卡 grid 渲染
        game_card = page.locator(HomePage.GAME_CARD)
        game_card.first.wait_for(state="attached", timeout=20000)

        # 點第一張遊戲卡，期待新分頁轉址到 provider
        from utils.game_launch_helper import launch_first_healthy_game, site_base_domain
        idx, url, host = launch_first_healthy_game(home, site_config.url, sh)
        assert host and site_base_domain(site_config.url) not in host, (
            f"遊戲未轉址至外部 provider，停在：{url}"
        )
