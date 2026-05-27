"""
視覺測試共用常數（RD）

站點專屬 BANNER_SELECTORS 放在此處；共用的 screenshot_with_mask / save_vr_screenshot
已集中至 utils/visual_helpers.py。
"""

# RD 動態 banner（首頁輪播大圖）：
#   - desktop-aspect-ratio：banner img 共用 class
#   - Page/Pc/：banner src 路徑模式
#   - 第三條保險：任何 class 含 banner 字樣的 img
BANNER_SELECTORS = [
    'img.desktop-aspect-ratio',
    'img[src*="Page/Pc/"]',
    '[class*="banner"] img',
]
