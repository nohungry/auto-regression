"""
通用彈窗處理 Helper
處理 dev 環境常見的伺服器錯誤彈窗
"""

from playwright.sync_api import Page


def dismiss_server_error_if_present(page: Page, timeout: int = 3000) -> bool:
    """
    檢查是否有「伺服器錯誤」彈窗，若有則點擊確定關閉。

    Returns:
        True  - 有彈窗且已關閉
        False - 沒有彈窗
    """
    confirm_btn = page.locator("button.toast-confirm-btn")

    try:
        confirm_btn.wait_for(state="visible", timeout=timeout)

        # 雙重確認：確認是伺服器錯誤彈窗，避免誤關其他彈窗
        error_text = page.locator("p", has_text="伺服器錯誤")
        if error_text.is_visible():
            confirm_btn.click()
            confirm_btn.wait_for(state="hidden", timeout=3000)
            print("[INFO] 已關閉「伺服器錯誤」彈窗")
            return True

    except Exception:
        pass  # 沒有彈窗，略過

    return False
