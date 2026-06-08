"""
視覺測試共用常數（KS — Super9娛樂城）

站點專屬 BANNER_SELECTORS 放在此處；共用的 screenshot_with_mask / save_vr_screenshot
已集中至 utils/visual_helpers.py。

KS 是 Nuxt (Vue)，金色英文/简体主題（預設 cn）。首頁主體為遊戲卡 grid
（div.grid.grid-cols-7），另含頂部 hero/banner 區。selector 全部 locale-agnostic（不綁文案）。

初版採結構性保守 selector（對齊 QW 模板）；若實跑後 home_shell 仍見動態 banner
未遮蔽，派 selector-explorer probe KS 首頁 DOM 補更精確 selector。
"""

BANNER_SELECTORS = [
    '.swiper-slide img',
    '[class*="banner"] img',
    'img[src*="banner"]',
    'img[src*="hero"]',
]
