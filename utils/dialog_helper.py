"""
通用彈窗 / Loading 處理 Helper
- dismiss_server_error_if_present：關閉伺服器錯誤彈窗
- wait_loading_if_present：等待 loading 狗動畫消失
"""

from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError


def dismiss_server_error_if_present(page: Page, timeout: int = 3000) -> bool:
    """
    檢查是否有「伺服器錯誤」彈窗，若有則點擊確定關閉。

    先用 count() 短路：button 不存在於 DOM → 立即回傳 False，不耗 timeout。
    僅在 button 已掛入 DOM 但尚未 visible 時才等待 timeout。

    Returns:
        True  - 有彈窗且已關閉
        False - 沒有彈窗
    """
    confirm_btn = page.locator("button.toast-confirm-btn")
    if confirm_btn.count() == 0:
        return False

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

    彈窗由伺服器 async 渲染，可能在 domcontentloaded 之後才插入 DOM，
    不能用 count() 短路，必須等 timeout。

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


def dismiss_dialog_mask_if_present(page: Page, timeout: int = 3000) -> bool:
    """
    關閉 dev-rd 首頁蓋板廣告（.dialog-mask + .dialog-container 結構）。

    與 dismiss_announcement_popup_if_present 不同：
    - announcement_popup 是 RC 站的 .popup-announcement-mask（Vue Transition fade-in），
      內含 button.close-circle-btn（多張輪播）
    - dialog-mask 是 RD 站的 Nuxt dialog 系統，蓋板廣告以 dialog-container 呈現，
      內含「關閉」button（class 含 bg-shade03 / lg:block）

    處理策略：
    1. 先試 click 蓋板的「關閉」按鈕
    2. 若 mask 沒消失（dev-rd 「關閉」按鈕 click 在 spike 階段實測無效），
       fallback 用 JS 強制 hide 整個 mask（測試的是登入而非蓋板邏輯，hack 可接受）

    Returns:
        True  - 有蓋板且已處理（click 或 force hide 任一成功）
        False - 沒蓋板
    """
    mask = page.locator(".dialog-mask")
    if mask.count() == 0:
        return False
    try:
        mask.first.wait_for(state="visible", timeout=timeout)
    except PlaywrightTimeoutError:
        return False

    # 路徑 A：嘗試 click 蓋板的「關閉」按鈕（在 dialog-container 內）
    close_btn = page.locator(".dialog-container button", has_text="關閉")
    if close_btn.count() > 0:
        try:
            close_btn.first.click(timeout=3000)
            mask.first.wait_for(state="hidden", timeout=3000)
            return True
        except PlaywrightTimeoutError:
            pass  # click 沒效或 mask 沒消失，走 fallback

    # 路徑 B：fallback — JS 強制 hide mask 與 dialog-container（避免 pointer-events 攔截）
    page.evaluate("""
        document.querySelectorAll('.dialog-mask, .dialog-container').forEach(el => {
            el.style.display = 'none';
            el.style.pointerEvents = 'none';
        });
    """)
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
