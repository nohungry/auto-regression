"""
視覺測試共用 helper（DLT）
供 test_visual.py 與 test_visual_regression.py 共用
"""

from playwright.sync_api import Page

BANNER_SELECTORS = [
    'img[src*="Page/Pc"]',
    'img[src*="MainPageImage"]',
    'img[src*="Games/dlt/"]',
    '[class*="banner"] img',
    '[class*="lg:via-[#FFF1A3]"]',
    '[class*="z-[98]"]',
]


def save_screenshot(img_bytes: bytes, name: str) -> None:
    """存檔截圖（不比對 baseline），供人工視覺確認用"""
    import os
    os.makedirs("screenshots/dlt/vr_reference", exist_ok=True)
    with open(f"screenshots/dlt/vr_reference/{name}", "wb") as f:
        f.write(img_bytes)


def screenshot_with_mask(page: Page, selectors: list[str], full_page: bool = True) -> bytes:
    """隱藏動態元素後截圖，截圖後還原可見性。
    同時停止 Swiper carousel autoplay 並回到第一張，確保截圖一致。
    """
    page.evaluate("""(selectors) => {
        window.__masked = [];
        selectors.forEach(sel => {
            document.querySelectorAll(sel).forEach(el => {
                window.__masked.push([el, el.style.visibility]);
                el.style.visibility = 'hidden';
            });
        });
        document.querySelectorAll('.swiper').forEach(el => {
            if (el.swiper) {
                el.swiper.autoplay.stop();
                el.swiper.slideTo(0, 0);
            }
        });
    }""", selectors)
    page.wait_for_timeout(300)
    try:
        return page.screenshot(full_page=full_page, animations="disabled")
    finally:
        page.evaluate("""() => {
            (window.__masked || []).forEach(([el, v]) => el.style.visibility = v);
            delete window.__masked;
        }""")
