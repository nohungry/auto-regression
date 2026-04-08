"""
通用彈窗 / Loading 處理 Helper
- dismiss_server_error_if_present：關閉伺服器錯誤彈窗
- wait_loading_if_present：等待 loading 狗動畫消失
"""

from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError


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
            confirm_btn.scroll_into_view_if_needed()
            confirm_btn.click()
            confirm_btn.wait_for(state="hidden", timeout=3000)
            print("[INFO] 已關閉「伺服器錯誤」彈窗")
            return True

    except PlaywrightTimeoutError:
        pass  # 沒有彈窗，略過

    return False


def dismiss_announcement_popup_if_present(page: Page, timeout: int = 3000) -> bool:
    """
    關閉老吉公告彈窗（popup-announcement-mask）。
    彈窗為多張輪播，每次點擊 close-circle-btn 僅推進一張，
    需持續點擊直到所有張數翻完後 popup 自動消失。

    Returns:
        True  - 有彈窗且已關閉
        False - 沒有彈窗
    """
    mask = page.locator(".popup-announcement-mask")
    try:
        mask.wait_for(state="visible", timeout=timeout)
    except PlaywrightTimeoutError:
        return False

    close_btn = page.locator("button.close-circle-btn")
    for _ in range(30):
        try:
            close_btn.wait_for(state="visible", timeout=1000)
            close_btn.click()
        except PlaywrightTimeoutError:
            break  # 按鈕消失 = 所有張數已翻完，popup 關閉
    return True


def wait_loading_if_present(page: Page, timeout: int = 2000) -> bool:
    """
    等待 loading 狗動畫（img[alt="Loading"] / ALL_Loading.gif）消失。
    若 timeout 內未出現則視為無 loading，直接回傳 False。

    出現時機：登入、導覽列切換、部分 sidebar 操作（user / mail / announce）。

    Returns:
        True  - 有出現過 loading 並已等待消失
        False - 未出現 loading
    """
    loading_img = page.locator('img[alt="Loading"]')
    try:
        loading_img.wait_for(state="visible", timeout=timeout)
        loading_img.wait_for(state="hidden", timeout=10000)
        return True
    except PlaywrightTimeoutError:
        return False
