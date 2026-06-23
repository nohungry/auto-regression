"""
視覺測試共用常數（RF — 金爺娛樂城）

站點專屬 BANNER_SELECTORS 放在此處；共用的 screenshot_with_mask / save_vr_screenshot
已集中至 utils/visual_helpers.py。

RF 是 Nuxt (Vue)，信用版，多語系（繁體中文/简体中文/English/Tiếng Việt/ภาษาไทย）。
首頁主體為遊戲卡 grid（.gameShowcaseSection__card），另含頂部主輪播 banner、跑馬燈。
selector 全部 locale-agnostic（不綁文案）。

probe 結果（dev-rf，2026-06-17）：
- 主輪播控制：.slider-arrow（prev/next 箭頭）、.slider-dot（dots 指示器）
- 跑馬燈：.marqueeBoxs / .marqueeBoxs__items（捲動文字）
- 帳號信用區（已登入）：.loginInBox（帳號名 + 餘額，動態數值）
- 遊戲展示輪播：.gameShowcaseSection（可能含輪播）
- 廣告 banner 圖：img[src*="banner"] / img[src*="Page/Pc"]
"""

BANNER_SELECTORS = [
    # 主輪播控制（箭頭 + dots）— 隱藏後截圖不見左右按鈕 / 底部點點
    '.slider-arrow',
    '.slider-dot',
    # 跑馬燈捲動文字
    '.marqueeBoxs',
    # 已登入狀態的帳號/餘額區（動態數值）
    '.loginInBox',
    # 遊戲展示輪播區
    '.gameShowcaseSection',
    # 廣告 banner 圖片
    'img[src*="banner"]',
    'img[src*="Page/Pc"]',
    '[class*="banner"] img',
]
