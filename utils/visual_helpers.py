"""
Visual Regression 共用基礎工具（跨站台）

站點專屬 BANNER_SELECTORS 仍保留在 `tests/<site_id>/feature/visual/helpers.py`，
因各站動態元素 selector 不同；此處只放不隨站台變動的截圖 / 遮罩邏輯。
"""

from __future__ import annotations

import os

from playwright.sync_api import Page


def save_vr_screenshot(img_bytes: bytes, site_id: str, name: str) -> None:
    """存 VR 參考截圖到 screenshots/<site_id>/vr_reference/<name>。
    不做 baseline 比對（跨環境解析度不穩定），供人工目視確認。
    """
    out_dir = f"screenshots/{site_id}/vr_reference"
    os.makedirs(out_dir, exist_ok=True)
    with open(f"{out_dir}/{name}", "wb") as f:
        f.write(img_bytes)


def screenshot_with_mask(page: Page, selectors: list[str], full_page: bool = True) -> bytes:
    """隱藏動態元素 + 停止 swiper autoplay 後截圖；結束後還原可見性。

    - 動態元素：透過 `visibility: hidden` 隱藏（`mask=` 只貼灰色覆蓋不阻止 layout 位移，無法穩定）
    - Swiper carousel：非所有站點的 `.swiper` 都有 swiper instance（RC 的 swiper-wrapper /
      swiper-slide 也命中 .swiper 但沒掛 instance），必須用 optional chaining 保護 autoplay/slideTo
    """
    page.evaluate(
        """(selectors) => {
        window.__masked = [];
        selectors.forEach(sel => {
            document.querySelectorAll(sel).forEach(el => {
                window.__masked.push([el, el.style.visibility]);
                el.style.visibility = 'hidden';
            });
        });
        document.querySelectorAll('.swiper').forEach(el => {
            if (el.swiper) {
                el.swiper.autoplay?.stop?.();
                el.swiper.slideTo?.(0, 0);
            }
        });
    }""",
        selectors,
    )
    page.wait_for_timeout(300)
    try:
        return page.screenshot(full_page=full_page, animations="disabled")
    finally:
        page.evaluate(
            """() => {
            (window.__masked || []).forEach(([el, v]) => el.style.visibility = v);
            delete window.__masked;
        }"""
        )
