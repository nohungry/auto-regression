"""選單 DOM 抽取輔助（站點無關）。

跨站共用只抽「與站點 DOM 無關的通用行為」，站點導覽語意（選單怎麼開、
容器 selector 是什麼）一律留在各站 POM —— 見 docs/decisions.md D-024。
"""

_LEAF_TEXTS_JS = """
(el, maxLen) => {
    const out = [];
    el.querySelectorAll('a,button,div,li,p').forEach(n => {
        const t = (n.textContent || '').trim().replace(/\\s+/g, ' ');
        if (t && t.length <= maxLen && n.children.length <= 1) out.push(t);
    });
    return [...new Set(out)];
}
"""


def leaf_menu_texts(menu_locator, max_len: int = 12) -> list:
    """回傳選單容器內的葉節點短文字（去重、保留出現順序）。

    抽自 LG/LU HomePage.user_menu_item_texts 完全相同的 evaluate（2026-08 收斂，D-024）。

    純 DOM 抽取、**不含任何站點 selector**：呼叫端傳入已開啟的選單容器 locator
    （LG = avatar dropdown panel、LU = 左側 sidebar），呼叫前須先開啟該選單。

    `max_len` 用於濾掉整段文案（只留選單項目這種短標籤）；`children.length <= 1`
    用於取葉節點，避免把容器 div 的合併文字也算進來。
    """
    return menu_locator.evaluate(_LEAF_TEXTS_JS, max_len)
