"""視窗 / 分頁尺寸輔助。

主要解決：`window.open` 另開的新分頁（如點遊戲卡 → 遊戲 launch new tab）
**不會繼承** conftest `page` fixture 的最大化視窗，預設尺寸偏小 →
互動座標錯位、截圖不完整。取得新分頁後須先呼叫 `maximize_page()`。

CDP no_viewport 模式下 `set_viewport_size` 無效，故改用 Browser.setWindowBounds。
headless（CI）環境無實體視窗，setWindowBounds 可能 no-op 或丟錯 → 全程 try/except
保護，最大化失敗不影響測試主流程。
"""

from playwright.sync_api import Page


def maximize_page(page: Page) -> None:
    """將指定分頁最大化（容錯：失敗不拋例外）。

    用於 window.open 另開的新分頁；headless CI 下可能無效，但不應讓測試失敗。
    """
    try:
        cdp = page.context.new_cdp_session(page)
    except Exception:
        return
    try:
        win = cdp.send("Browser.getWindowForTarget")
        cdp.send(
            "Browser.setWindowBounds",
            {"windowId": win["windowId"], "bounds": {"windowState": "maximized"}},
        )
    except Exception:
        pass
    finally:
        try:
            cdp.detach()
        except Exception:
            pass
