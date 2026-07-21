"""
通用彈窗 / Loading 處理 Helper
- dismiss_server_error_if_present：關閉伺服器錯誤彈窗
- wait_loading_if_present：等待 loading 狗動畫消失
- wait_login_loading：登入流程 loading 等待＋步驟截圖（RC/RD/RE LoginPage 共用）
- clear_stuck_leave_overlay_if_present：清卡死的 Vue 離場動畫全屏遮罩（KS/RD dev bug 家族）
"""

from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError

from utils.screenshot_helper import get_screenshotter


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
    清除 RC 公告大圖輪播彈窗（popup-announcement-mask）。

    策略（2026-05-19 升級）：注入永久 CSS killer + MutationObserver 持續 enforce。

    為何不走「click ✕ 翻完所有張數」路徑：
    1. dev-rc 已知 bug — 螢幕不夠大時 ✕ 按鈕在 viewport 外完全點不到。
    2. 即便 click 成功，Vue + 伺服器 async 渲染會在 click 與後續 login 操作之間
       重新 mount popup（timing race）— 造成 login_trigger_btn.click() 仍被攔截。

    為何 2026-05-19 加 MutationObserver：
    - probe 確認 CSS killer 注入 <head> 後會被 SPA hydration 清除；
      隨後互動（如 sidebar click）會觸發 Vue 重新渲染 mask，opacity 從 0 跳回 1。
    - MO 持續監視 documentElement：
        a) 偵測 killer style 被移除 → 立即重注
        b) 偵測 .popup-announcement-mask 重新 mount → 立即 remove
    - 每 page 只裝一個 MO（`window.__rc_popup_announcement_killer_mo` guard），
      page reload 後 JS state 重設、下次 caller 再呼叫時重新安裝。

    本 helper 對非 RC 站（無 popup-announcement-mask 元素）為 no-op，安全。
    timeout 參數保留以維持 caller 簽名相容，內部不使用。

    注意：`tests/rc/feature/announcement_popup/test_announcement_popup.py` 用 `page.goto`
    直接走（不經 `LoginPage.goto()`），不會觸發此 killer，popup 行為驗證不受影響。

    Returns:
        True - 注入完成（不論 popup 當下是否在 DOM）
    """
    page.evaluate("""
        (() => {
            const KILLER_ID = '__rc_popup_announcement_killer';
            const KILLER_CSS = '.popup-announcement-mask { display: none !important; pointer-events: none !important; opacity: 0 !important; }';

            function installKiller() {
                if (!document.getElementById(KILLER_ID)) {
                    const style = document.createElement('style');
                    style.id = KILLER_ID;
                    style.textContent = KILLER_CSS;
                    (document.head || document.documentElement).appendChild(style);
                }
            }

            // 立即執行：注入 killer + 清一次目前已存在的 mask（後續由 CSS 處理）
            installKiller();
            document.querySelectorAll('.popup-announcement-mask').forEach(el => el.remove());
            if (document.body) document.body.classList.remove('dialog-open');

            // MutationObserver 只盯 <head> 的 style 是否被 SPA hydration 清除 → 立即重注。
            // 不動 mask DOM（避免 race Vue 進場動畫導致 sibling 元素如 login modal 構建失敗）。
            // CSS `display:none !important + opacity:0` 已足以視覺隱藏 + 失效 pointer-events。
            if (!window.__rc_popup_announcement_killer_mo) {
                const mo = new MutationObserver(installKiller);
                const target = document.head || document.documentElement;
                mo.observe(target, { childList: true });
                window.__rc_popup_announcement_killer_mo = mo;
            }
        })()
    """)
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


def wait_login_loading(page: Page) -> None:
    """
    等待 loading 狗動畫（img[alt="Loading"] / ALL_Loading.gif）出現並消失，含步驟截圖。
    RC/RD/RE LoginPage 登入流程共用；若 2 秒內未出現（登入失敗或速度極快）則略過。
    """
    sh = get_screenshotter(page)
    loading_img = page.locator('img[alt="Loading"]')
    try:
        loading_img.wait_for(state="visible", timeout=2000)
        if sh: sh.capture(loading_img, "loading_登入中")
        loading_img.wait_for(state="hidden", timeout=10000)
        if sh: sh.full_page("loading_完成_進入首頁")
    except PlaywrightTimeoutError:
        pass  # loading 未出現或已快速消失，略過


def clear_stuck_leave_overlay_if_present(page: Page, settle_timeout: int = 3000) -> bool:
    """
    清掉卡死的 Vue 離場動畫全屏遮罩（.fade-leave-active）。

    dev 環境偶發 Vue Transition 離場後元素不從 DOM 移除（KS 2026-06 首見、
    RD 2026-07-21 於導覽點擊重現）：彈窗本身已正常關閉，但殘留的 fixed 全屏
    遮罩持續攔截 pointer events，後續 click 以 "subtree intercepts pointer
    events" timeout。此處僅隱藏殘留遮罩，非掩蓋產品彈窗邏輯。

    先等 settle_timeout 給正常離場動畫收尾（正常 <1s 即 detach）；仍殘留才 JS 隱藏。

    Returns:
        True  - 有殘留遮罩且已強制隱藏
        False - 無殘留（不存在或已自行 detach）
    """
    overlay = page.locator(".fade-leave-active")
    if overlay.count() == 0:
        return False
    try:
        overlay.first.wait_for(state="detached", timeout=settle_timeout)
        return False
    except PlaywrightTimeoutError:
        page.evaluate(
            """() => {
            document.querySelectorAll('.fade-leave-active').forEach(m => {
                m.style.display = 'none';
            });
        }"""
        )
        return True
