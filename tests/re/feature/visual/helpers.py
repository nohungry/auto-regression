"""
視覺測試共用常數（RE / BeWin）

站點專屬 BANNER_SELECTORS 放在此處；共用的 screenshot_with_mask / save_vr_screenshot
已集中至 utils/visual_helpers.py。

RE 與 RC 共用 t9platform 平台 banner 結構，沿用相同 selector。
"""

BANNER_SELECTORS = [
    'img.desktop-aspect-ratio',
    'img[src*="Page/Pc/"]',
    '[class*="banner"] img',
]
