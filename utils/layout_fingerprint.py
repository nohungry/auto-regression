"""
DOM 指紋（Layout Fingerprint）工具 — 方向 5

用途：
    為指定頁面抓取 DOM 結構指紋（tag / class / text / font-size / visibility），
    序列化為穩定 JSON，跨環境比對。不含 pixel 座標，因此不受螢幕大小、
    字型渲染、DPI 影響。

使用方式：
    from utils.layout_fingerprint import assert_fingerprint

    assert_fingerprint(page, "tests/dlt/__fingerprints__/locale-tw-login.json")

    # 首次執行若 baseline 不存在，會自動建立並通過。
    # 若要強制更新 baseline，可刪除對應 JSON 檔案後重跑。

設計原則：
    - 只記錄「結構 + 文字 + CSS 定義值」，不記錄 bbox/left/top 等 layout 座標
    - 預設鎖定可見的互動元素與標題（button/a/input/h1~h3/p.h*/label）
    - 可傳入自訂 selector 與 ignore regex
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Optional

from playwright.sync_api import Page

# 預設抓取範圍：互動元素 + 主要文字
_DEFAULT_SELECTORS = [
    "button",
    "a",
    "input",
    "label",
    "h1", "h2", "h3",
    '[role="button"]',
    '[role="tab"]',
]

_CAPTURE_JS = r"""
(selectors) => {
    const items = [];
    const seen = new Set();
    for (const sel of selectors) {
        for (const el of document.querySelectorAll(sel)) {
            if (seen.has(el)) continue;
            seen.add(el);
            const rect = el.getBoundingClientRect();
            const style = window.getComputedStyle(el);
            const visible =
                rect.width > 0 && rect.height > 0 &&
                style.visibility !== 'hidden' && style.display !== 'none';
            if (!visible) continue;
            const text = (el.textContent || '').trim().replace(/\s+/g, ' ').slice(0, 80);
            items.push({
                tag: el.tagName.toLowerCase(),
                cls: String(el.className || '').split(' ').slice(0, 3).join(' ').slice(0, 60),
                text: text,
                placeholder: el.getAttribute('placeholder') || '',
                font_size: style.fontSize,
                font_weight: style.fontWeight,
            });
        }
    }
    return items;
}
"""


def capture_fingerprint(
    page: Page,
    selectors: Optional[list[str]] = None,
    ignore_text_patterns: Optional[list[str]] = None,
) -> dict:
    """抓取頁面當前的 DOM 指紋。"""
    items = page.evaluate(_CAPTURE_JS, selectors or _DEFAULT_SELECTORS)

    if ignore_text_patterns:
        regexes = [re.compile(p) for p in ignore_text_patterns]
        items = [
            it for it in items
            if not any(r.search(it["text"]) for r in regexes)
        ]

    # 穩定排序（tag → text → cls），確保 diff 不受 DOM 順序微動影響
    items.sort(key=lambda it: (it["tag"], it["text"], it["cls"]))

    return {"version": 1, "count": len(items), "items": items}


def _write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )


def _diff_summary(actual: dict, baseline: dict) -> str:
    a_items = actual.get("items", [])
    b_items = baseline.get("items", [])

    def _key(it):
        return (it["tag"], it["text"], it.get("placeholder", ""))

    a_keys = {_key(it) for it in a_items}
    b_keys = {_key(it) for it in b_items}

    added = sorted(a_keys - b_keys)
    removed = sorted(b_keys - a_keys)

    lines = [
        f"Count: baseline={len(b_items)} actual={len(a_items)}",
    ]
    if added:
        lines.append(f"Added ({len(added)}):")
        for tag, text, ph in added[:10]:
            lines.append(f"  + <{tag}> text='{text}' placeholder='{ph}'")
        if len(added) > 10:
            lines.append(f"  ... and {len(added) - 10} more")
    if removed:
        lines.append(f"Removed ({len(removed)}):")
        for tag, text, ph in removed[:10]:
            lines.append(f"  - <{tag}> text='{text}' placeholder='{ph}'")
        if len(removed) > 10:
            lines.append(f"  ... and {len(removed) - 10} more")
    return "\n".join(lines)


def assert_fingerprint(
    page: Page,
    baseline_path: str | Path,
    selectors: Optional[list[str]] = None,
    ignore_text_patterns: Optional[list[str]] = None,
) -> None:
    """
    與 baseline JSON 比對指紋。
    - 若 baseline 不存在：寫入當前指紋作為新 baseline，測試通過。
    - 若 baseline 存在且結構相符：通過。
    - 若結構不同：寫 `<baseline>.actual.json` 供 diff，AssertionError。
    """
    actual = capture_fingerprint(page, selectors, ignore_text_patterns)
    path = Path(baseline_path)

    if not path.exists():
        _write_json(path, actual)
        return

    baseline = json.loads(path.read_text(encoding="utf-8"))

    def _key_set(fp):
        return {(it["tag"], it["text"], it.get("placeholder", "")) for it in fp["items"]}

    if _key_set(actual) == _key_set(baseline):
        return

    actual_path = path.with_suffix(".actual.json")
    _write_json(actual_path, actual)
    raise AssertionError(
        f"Layout fingerprint 與 baseline 不符\n"
        f"  baseline: {path}\n"
        f"  actual  : {actual_path}\n\n"
        f"{_diff_summary(actual, baseline)}\n\n"
        f"若此變更為預期的產品更新，請刪除 baseline 檔重跑以重建。"
    )
