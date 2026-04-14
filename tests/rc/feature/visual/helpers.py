"""
視覺測試共用常數（RC）

站點專屬 BANNER_SELECTORS 放在此處；共用的 screenshot_with_mask / save_vr_screenshot
已集中至 utils/visual_helpers.py。
"""

BANNER_SELECTORS = [
    'img.desktop-aspect-ratio',
    'img[src*="Page/Pc/"]',
    '[class*="banner"] img',
]
