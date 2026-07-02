"""
可判定等待 helper — 取代散落的硬等固定毫秒（`page.wait_for_timeout(N)`）。

設計原則：
- 只封裝「有明確 DOM 可判定信號」的等待；真動畫/第三方渲染（visual / game）不在此列。
- 薄封裝 Playwright `expect` 的自動輪詢，讓 POM 讀值前的等待語意化、跨站共用。
"""

import re

from playwright.sync_api import Locator, expect

# 任一非空白字元 → 判定元素文字「已填入內容」（排除空字串 / 純空白 loading 態）
_NONEMPTY = re.compile(r"\S")


def wait_for_nonempty_text(locator: Locator, timeout: int = 10000) -> None:
    """等 locator 文字出現非空白內容後返回（取代『點擊開 dialog → 硬等固定毫秒 → 讀值』）。

    用於「元素會非同步填入值、但填入時機不定」的讀值場景（如後台 dialog 內的餘額
    label）。比固定 `wait_for_timeout` 穩健：慢環境不會太早讀到空值、快環境不空等。

    逾時（元素未出現或始終空白）由 Playwright 拋 AssertionError，不靜默吞掉。
    """
    expect(locator).to_contain_text(_NONEMPTY, timeout=timeout)
