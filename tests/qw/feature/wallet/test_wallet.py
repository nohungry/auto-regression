"""
QW 錢包功能測試（LM來財娛樂城）
QW-WALLET-001 ~ 004

probe 2026-06-25：
- 首頁 nav 右側有 3 個 a.shortcut-tile（真實 <a href>）：
    存款 → /member-center?type=Deposit
    轉帳 → /member-center?type=GameWallets
    取款 → /member-center?type=Withdrawal
- member-center 內也有相同 3 個 <a> shortcut-tile 連結。

驗證範圍：
  WALLET-001：首頁 shortcut-tile 存款/轉帳/取款 均可見（read-only UI 結構）
  WALLET-002：點存款 tile → URL 含 /member-center?type=Deposit
  WALLET-003：點轉帳 tile → URL 含 /member-center?type=GameWallets
  WALLET-004：點取款 tile → URL 含 /member-center?type=Withdrawal

斷言策略：
- 只驗 URL 跳轉（read-only，不做實際金流）
- type= 值用 URL 字串比對，不驗頁面 DOM 細節（避免後台佈局改動造成 flaky）
- Nuxt SPA 路由用 wait_for_function 偵測 window.location.href 變更

注意：QW shortcut-tile 為真實 <a href>（非 JS handler），click() 可直接觸發導航。
"""

import pytest
from playwright.sync_api import Page, expect
from pages.factory import get_home_page_class
from utils.screenshot_helper import get_screenshotter


HomePage = get_home_page_class("qw")


@pytest.mark.p1
@pytest.mark.qw
@pytest.mark.wallet
class TestWallet:
    """QW-WALLET-001 ~ 004：首頁 shortcut-tile 存提入口"""

    def test_wallet_shortcuts_visible(self, class_logged_in_page: Page, go_home):
        """QW-WALLET-001：首頁 shortcut-tile（存款/轉帳/取款）均可見

        斷言策略：
        - a.shortcut-tile 共 3 個（存款/轉帳/取款）
        - 每個 tile 均 visible（read-only UI 健康度）
        不驗文案（多語系站），只驗 count 與 visible。
        """
        page = class_logged_in_page
        home = HomePage(page)
        sh = get_screenshotter(page)

        # 等 Nuxt 完全 hydrate
        page.wait_for_timeout(800)

        tiles = home.wallet_shortcut_tiles()
        tile_count = tiles.count()
        if sh: sh.full_page(f"verify_shortcut_tile_count_{tile_count}")

        assert tile_count >= 3, (
            f"首頁 shortcut-tile 應至少有 3 個（存款/轉帳/取款），實際：{tile_count}"
        )

        # 驗各 tile 可見
        for i in range(min(tile_count, 3)):
            tile = tiles.nth(i)
            tile.scroll_into_view_if_needed()
            if sh: sh.capture(tile, f"verify_shortcut_tile_{i}")
            expect(tile).to_be_visible()

    @pytest.mark.parametrize(
        "type_key,label",
        [
            ("Deposit", "存款"),
            ("GameWallets", "轉帳"),
            ("Withdrawal", "取款"),
        ],
        ids=["Deposit", "GameWallets", "Withdrawal"],
    )
    def test_wallet_link_navigates(
        self, class_logged_in_page: Page, go_home, type_key: str, label: str
    ):
        """QW-WALLET-002/003/004：點 shortcut-tile 後 URL 導向 /member-center?type=<key>

        斷言策略：
        - click shortcut-tile（真實 <a href>）→ Nuxt SPA pushState
        - wait_for_function 偵測 window.location.href 含 type=<key>
        - 驗 URL 含 /member-center（正確頁面）及 type=<key>（正確 tab）
        不驗頁面 DOM 細節（避免後台佈局改動造成 flaky）。
        """
        page = class_logged_in_page
        home = HomePage(page)
        sh = get_screenshotter(page)

        # 等 Nuxt 完全 hydrate
        page.wait_for_timeout(800)

        if sh: sh.full_page(f"before_click_{type_key}_tile")

        home.click_shortcut_tile(type_key)

        # Nuxt SPA pushState 路由，wait_for_function 輪詢 location.href
        page.wait_for_function(
            f"() => window.location.href.includes('type={type_key}')",
            timeout=12000,
        )
        current_url = page.url
        if sh: sh.full_page(f"verify_wallet_{type_key}_url_{current_url.split('?')[-1]}")

        assert "/member-center" in current_url, (
            f"預期進 /member-center，實際 URL：{current_url}"
        )
        assert f"type={type_key}" in current_url, (
            f"預期 URL 含 type={type_key}，實際 URL：{current_url}"
        )
