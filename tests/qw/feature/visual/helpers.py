"""
視覺測試共用常數（QW）

站點專屬 BANNER_SELECTORS 放在此處；共用的 screenshot_with_mask / save_vr_screenshot
已集中至 utils/visual_helpers.py。

QW 是 Nuxt (Vue) + 多語系（LaiBetLanguage cookie）。
selector 全部 locale-agnostic（不綁文案）。

候選來源（2026-05-22 probe）：
  - QW 首頁有 swiper hero banner，probe 看到「電子 真人 捕魚 棋牌 體育 彩票 鬥雞 優惠」分類
  - banner 圖片路徑待 probe 確認；先以結構性 selector 覆蓋常見 pattern：
      .swiper-slide img    — swiper slide 內的 banner 圖（最常見結構）
      [class*="banner"] img — 任何 class 含 banner 字串的容器內的 img
      img[src*="banner"]   — src 路徑含 banner 的 img（CMS 圖片命名規律）
      img[src*="hero"]     — src 路徑含 hero 的 img（部分站台慣例）

  若實跑後發現 mask 未命中（swiper 仍自動輪播 / 圖片未隱藏），
  請回報主 context 派 selector-explorer probe 首頁 DOM，補充更精確的 selector。
"""

BANNER_SELECTORS = [
    '.swiper-slide img',
    '[class*="banner"] img',
    'img[src*="banner"]',
    'img[src*="hero"]',
]
