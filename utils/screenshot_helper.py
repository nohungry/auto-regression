"""
截圖工具
- ScreenshotHelper：管理測試的截圖序列（資料夾 + 步驟計數 + README.md 報告）
- attach/detach/get：讓 POM 方法不需傳參也能取得 screenshotter
- _highlight_and_screenshot：在元素上畫紅框 + 標籤後截圖

截圖存放路徑：screenshots/<site_id>/<timestamp>/<test_name>/<001_label>.png
測試說明文件：screenshots/<site_id>/<timestamp>/<test_name>/README.md
"""

import re
from datetime import datetime
from pathlib import Path
from playwright.sync_api import Page, Locator

SCREENSHOTS_DIR = Path("screenshots")

# 整個 session 共用同一個 timestamp（第一次建立時設定）
_SESSION_TIMESTAMP: str | None = None


def _get_session_timestamp() -> str:
    global _SESSION_TIMESTAMP
    if _SESSION_TIMESTAMP is None:
        _SESSION_TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M")
    return _SESSION_TIMESTAMP

# page id -> ScreenshotHelper，讓 POM 可以免傳參取得
_registry: dict[int, "ScreenshotHelper"] = {}


def attach_screenshotter(page: Page, sh: "ScreenshotHelper") -> None:
    _registry[id(page)] = sh


def detach_screenshotter(page: Page) -> None:
    _registry.pop(id(page), None)


def get_screenshotter(page: Page) -> "ScreenshotHelper | None":
    return _registry.get(id(page))


def _sanitize(name: str) -> str:
    """轉為安全的資料夾/檔名（保留中文）"""
    return re.sub(r'[^\w\-\u4e00-\u9fff]', '_', name)[:80]


# 將操作前綴對應至繁體中文動詞
_LABEL_PREFIX_ZH = {
    "click":  "點擊",
    "fill":   "填入",
    "verify": "驗證",
    "scroll": "捲動至",
    "select": "選取",
    "hover":  "移至",
    "full":   "全頁截圖",
}


def _label_to_zh(label: str) -> str:
    """將 'click_登入按鈕' 轉為 '點擊 登入按鈕'，其餘原樣回傳。"""
    for prefix, zh in _LABEL_PREFIX_ZH.items():
        if label.startswith(f"{prefix}_"):
            rest = label[len(prefix) + 1:].replace("_", " ")
            return f"{zh} {rest}"
    return label.replace("_", " ")


class ScreenshotHelper:
    """
    每個測試一個 ScreenshotHelper 實例，截圖自動編號存入專屬資料夾，
    測試結束後自動產生 README.md 操作流程說明。

    在 POM 方法中使用：
        from utils.screenshot_helper import get_screenshotter
        sh = get_screenshotter(self.page)
        if sh:
            sh.capture(self.some_locator, "click_動作描述")
    """

    def __init__(self, page: Page, test_name: str, description: str = "", site_id: str = "unknown"):
        self.page = page
        timestamp = _get_session_timestamp()
        self.folder = SCREENSHOTS_DIR / site_id / timestamp / _sanitize(test_name)
        self.folder.mkdir(parents=True, exist_ok=True)
        self._test_name = test_name
        self._description = description.strip()
        self._step = 0
        self._steps: list[dict] = []  # {step, label, filename}

    def capture(self, locator: Locator, label: str = "action") -> Path:
        """標示元素（紅框 + 標籤）後截圖，回傳截圖路徑。"""
        self._step += 1
        filename = f"{self._step:03d}_{_sanitize(label)}.png"
        filepath = self.folder / filename
        _highlight_and_screenshot(self.page, locator, filepath, label)
        self._steps.append({"step": self._step, "label": label, "filename": filename})
        return filepath

    def full_page(self, label: str = "full") -> Path:
        """不標示元素，直接截全頁圖。"""
        self._step += 1
        filename = f"{self._step:03d}_{_sanitize(label)}.png"
        filepath = self.folder / filename
        self.page.screenshot(path=str(filepath))
        self._steps.append({"step": self._step, "label": label, "filename": filename})
        return filepath

    def generate_report(self) -> None:
        """將本次測試的操作步驟寫成 README.md，存於截圖資料夾。"""
        if not self._steps:
            return

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        lines: list[str] = []

        # 標題
        lines += [
            f"# {self._test_name}",
            "",
        ]

        # 測試說明（來自 docstring）
        if self._description:
            lines += [
                f"> {self._description}",
                "",
            ]

        lines += [
            f"**執行時間：** {now}",
            f"**操作步驟總數：** {len(self._steps)} 步",
            "",
            "---",
            "",
            "## 操作步驟",
            "",
        ]

        # 每個步驟
        for s in self._steps:
            zh = _label_to_zh(s["label"])
            lines += [
                f"### 步驟 {s['step']:03d}｜{zh}",
                "",
                f"![步驟 {s['step']:03d} — {zh}]({s['filename']})",
                "",
            ]

        report_path = self.folder / "README.md"
        report_path.write_text("\n".join(lines), encoding="utf-8")


def _highlight_and_screenshot(
    page: Page, locator: Locator, filepath: Path, label: str = ""
) -> None:
    """
    取得元素 bounding box → 注入紅框標籤 overlay → 截圖 → 移除 overlay。
    若取不到 bounding box（元素在 viewport 外 / CSS 隱藏）則直接截圖不標示。
    """
    box = None
    try:
        box = locator.first.bounding_box(timeout=3000)
    except Exception:
        pass

    if box:
        page.evaluate(
            """([x, y, w, h, lbl]) => {
                const old = document.getElementById('__pw_highlight__');
                if (old) old.remove();

                const wrap = document.createElement('div');
                wrap.id = '__pw_highlight__';

                // 紅框
                const frame = document.createElement('div');
                frame.style.cssText = [
                    'position:fixed',
                    `left:${x - 4}px`,
                    `top:${y - 4}px`,
                    `width:${w + 8}px`,
                    `height:${h + 8}px`,
                    'border:3px solid #ff3333',
                    'border-radius:4px',
                    'background:rgba(255,51,51,0.07)',
                    'box-shadow:0 0 0 3px rgba(255,51,51,0.2)',
                    'pointer-events:none',
                    'z-index:2147483647',
                ].join(';');
                wrap.appendChild(frame);

                // 標籤
                if (lbl) {
                    const tag = document.createElement('div');
                    tag.textContent = lbl;
                    tag.style.cssText = [
                        'position:fixed',
                        `left:${x - 4}px`,
                        `top:${Math.max(4, y - 26)}px`,
                        'background:#ff3333',
                        'color:#fff',
                        'padding:2px 8px',
                        'border-radius:3px 3px 3px 0',
                        'font:bold 12px/1.5 sans-serif',
                        'white-space:nowrap',
                        'pointer-events:none',
                        'z-index:2147483647',
                    ].join(';');
                    wrap.appendChild(tag);
                }

                document.body.appendChild(wrap);
            }""",
            [box['x'], box['y'], box['width'], box['height'], label]
        )

    try:
        page.screenshot(path=str(filepath))
    finally:
        if box:
            page.evaluate("""() => {
                const el = document.getElementById('__pw_highlight__');
                if (el) el.remove();
            }""")
