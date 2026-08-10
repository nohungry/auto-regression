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

    def test_deposit_entry_offers_next_step(self, class_logged_in_page: Page, go_home):
        """QW-WALLET-005：點存款入口後，頁面提供明確可操作的下一步（probe 2026-08-10）

        WALLET-002 只驗「URL 瞬間變成 type=Deposit」——實測那之後約 1 秒，未綁銀行卡的
        帳號會被 toast「請先綁定銀行卡」導向 type=Withdrawal 的銀行卡管理區。也就是說
        WALLET-002 綠燈並不代表存款頁真的可用，本條補上「最終落點可操作」這一層。

        斷言策略：不斷言瞬時 toast（生命週期約 1 秒，硬等會 flaky），改等最終落點的
        可操作元素——「新增銀行卡」入口可見。這同時守住 bug #11 那類缺陷
        （前端拿到錯誤卻不渲染、留下空白頁無下一步）。

        ⚠️ 現況綁定：本條反映「測試帳號未綁卡」的守衛路徑。若日後帳號綁了銀行卡，
        存款頁不再被導走，本條會 fail —— 屆時應重新 probe 存款渠道 DOM，改驗渠道呈現
        （LU 已有該路徑的模板：LU-WALLET-006）。fail 即為測試資料變更的訊號，不是誤報。
        """
        page = class_logged_in_page
        home = HomePage(page)
        sh = get_screenshotter(page)

        home.click_shortcut_tile("Deposit")

        add_bank_btn = page.locator("button.add-bank").first
        expect(add_bank_btn).to_be_visible(timeout=15000)
        if sh: sh.capture(add_bank_btn, "verify_存款守衛_導向綁卡入口")

        assert "/member-center" in page.url, f"預期停在會員中心，實際 URL：{page.url}"

    def test_balance_displayed(self, class_logged_in_page: Page, go_home):
        """QW-WALLET-006：nav 餘額登入後可見且為合法金額字串（probe 2026-08-10）

        補齊與 LU-WALLET-001/002、LG-WALLET-001 的對齊（QW 先前無餘額斷言，
        已登入信號只有 avatar）。餘額元素用**內容定位**（"$" + 數字），不綁色票 class
        ——QW 該元素僅掛任意 Tailwind 色票，色票會隨改版變動。

        斷言只驗「非空 + 含數字」，不寫死金額：餘額會被後台 top_up 測試改動。
        """
        page = class_logged_in_page
        home = HomePage(page)
        sh = get_screenshotter(page)

        expect(home.balance).to_be_visible(timeout=10000)
        home.balance.scroll_into_view_if_needed()
        text = home.balance.inner_text().strip()
        if sh: sh.capture(home.balance, f"verify_餘額顯示_{text}")

        assert text, "餘額文字為空"
        assert any(c.isdigit() for c in text), f"餘額文字不含數字：{text!r}"
