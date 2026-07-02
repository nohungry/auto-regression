"""
可判定等待 helper — 取代散落的硬等固定毫秒（`page.wait_for_timeout(N)`）。

設計原則：
- 只封裝「有明確 DOM 可判定信號」的等待；真動畫/第三方渲染（visual / game）不在此列。
- 薄封裝 Playwright `expect` 的自動輪詢，讓 POM 讀值前的等待語意化、跨站共用。
"""

import re
from typing import Pattern, Union

from playwright.sync_api import Locator, expect

# 任一非空白字元 → 判定元素文字「已填入內容」（排除空字串 / 純空白 loading 態）
_NONEMPTY = re.compile(r"\S")


def wait_for_text_matches(
    locator: Locator, pattern: Union[str, Pattern], timeout: int = 10000
) -> None:
    """等 locator 文字（contains 語意）出現符合 pattern 的內容後返回。

    取代『點擊開 dialog → 硬等固定毫秒 → 讀值』：當要讀的值混在其它文字中（如
    後台 dialog 的「剩餘額度 12,345」），需用 pattern 判定該值『數字部分已載入』，
    而非只判定元素非空（其它固定文案會讓非空太早成立）。

    逾時（始終不符）由 Playwright 拋 AssertionError，不靜默吞掉。
    """
    expect(locator).to_contain_text(pattern, timeout=timeout)


def wait_for_nonempty_text(locator: Locator, timeout: int = 10000) -> None:
    """等 locator 文字出現非空白內容後返回（wait_for_text_matches 的 `\\S` 特例）。

    用於「元素會非同步填入值、且該元素只含那個值」的讀值場景（如 rf dashboard
    dialog 內獨立的餘額 span）。比固定 `wait_for_timeout` 穩健：慢環境不會太早讀
    到空值、快環境不空等。
    """
    wait_for_text_matches(locator, _NONEMPTY, timeout=timeout)
