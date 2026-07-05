"""
截圖工具
- ScreenshotHelper：管理測試的截圖序列（資料夾 + 步驟計數 + README.md 報告）
- attach/detach/get：讓 POM 方法不需傳參也能取得 screenshotter
- _highlight_and_screenshot：在元素上畫紅框 + 標籤後截圖

截圖存放路徑：screenshots/<site_id>/<timestamp>/<category>/<test_name>/<001_label>.png
測試說明文件：screenshots/<site_id>/<timestamp>/<category>/<test_name>/README.md
category 由 conftest auto_screenshot 自動判斷：feature/ 下為 feature，其餘為 smoke
"""

import json
import re
from datetime import datetime
from pathlib import Path
from playwright.sync_api import Page, Locator

SCREENSHOTS_DIR = Path("screenshots")

# 截圖超時（毫秒）。Playwright 預設 30 秒且會等 document.fonts.ready，
# 某些環境（字型第三方失敗但未 reject）會永遠 hang。縮短避免阻塞測試，
# 截圖純觀察性質，失敗不應 fail 測試。
_SCREENSHOT_TIMEOUT_MS = 10000

# 圈選判定用常數
_BBOX_TIMEOUT_MS = 3000      # 取 bounding_box 超時
_SCROLL_TIMEOUT_MS = 2000    # capture 前自動捲入視野的短超時（避免阻塞）
_OVERSIZE_RATIO = 0.85       # box 面積 > 視窗面積此比例 → 判定「圈了等於沒圈」

# 圈選失敗原因 → 繁中說明（README badge / audit 報告共用）
_REASON_ZH = {
    "ok":          "正常",
    "full_page":   "整頁截圖",
    "no_match":    "命中 0 元素",
    "no_box":      "取不到座標（元素隱藏或 detached）",
    "zero_area":   "元素零面積",
    "offscreen":   "元素在視窗外",
    "bbox_error":  "座標取得逾時",
    "not_written": "截圖未寫出",
}

# 圈選失敗判定：這些 reason 代表「呼叫了 capture 卻沒真的圈到目標」
_FAIL_REASONS = {"no_match", "no_box", "zero_area", "offscreen", "bbox_error"}


def _step_flawed(s: dict) -> bool:
    """step 是否「有瑕疵」＝ 沒真的圈到 / 多命中 / 框過大 / 截圖未寫出。

    written 用 `.get("written") is False` 判定：舊 steps.json 無此欄回 None ≠ False，
    向後相容不誤報。full_page 步驟只會因 written is False 命中此判定。
    """
    return (
        s.get("highlighted") is False
        or bool(s.get("multi_match"))
        or bool(s.get("oversize"))
        or s.get("written") is False
    )

# 整個 session 共用同一個 timestamp（第一次建立時設定）
_SESSION_TIMESTAMP: str | None = None


def _get_session_timestamp() -> str:
    global _SESSION_TIMESTAMP
    if _SESSION_TIMESTAMP is None:
        _SESSION_TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M")
    return _SESSION_TIMESTAMP

# page id -> ScreenshotHelper，讓 POM 可以免傳參取得
_registry: dict[int, "ScreenshotHelper"] = {}

# session 級圈選稽核累加器：generate_report() 時把失敗步驟 append 進來，
# pytest_sessionfinish 呼叫 write_highlight_audit() 依 (site, timestamp) 彙整成報告。
# 每筆：{site, timestamp, category, test, step, label, reason, match_count, path}
_AUDIT_RECORDS: list[dict] = []


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

    def __init__(self, page: Page, test_name: str, description: str = "", site_id: str = "unknown", category: str = "smoke"):
        self.page = page
        timestamp = _get_session_timestamp()
        self.folder = SCREENSHOTS_DIR / site_id / timestamp / category / _sanitize(test_name)
        self.folder.mkdir(parents=True, exist_ok=True)
        self._test_name = test_name
        self._description = description.strip()
        self._site_id = site_id
        self._category = category
        self._timestamp = timestamp
        self._step = 0
        self._steps: list[dict] = []  # {step, label, filename, kind, highlighted, reason, ...}

    def capture(self, locator: Locator, label: str = "action") -> Path:
        """標示元素（紅框 + 標籤）後截圖，回傳截圖路徑。

        圈選結果（是否真的圈到、原因、命中數）會記進 step metadata，
        供 README badge 與 session 稽核報告判定「哪些截圖沒準確圈到元素」。
        """
        self._step += 1
        filename = f"{self._step:03d}_{_sanitize(label)}.png"
        filepath = self.folder / filename
        status = _highlight_and_screenshot(self.page, locator, filepath, label)
        self._steps.append({
            "step": self._step,
            "label": label,
            "filename": filename,
            "kind": "capture",
            "highlighted": status["highlighted"],
            "reason": status["reason"],
            "match_count": status["match_count"],
            "multi_match": status["multi_match"],
            "oversize": status["oversize"],
            "written": status["written"],
        })
        return filepath

    def full_page(self, label: str = "full", page: Page | None = None) -> Path:
        """不標示元素，直接截全頁圖。截圖失敗（timeout / page closed）不拋出。

        page 可指定替代 page（例如遊戲新分頁 popup），檔案仍輸出到同一 helper 資料夾，
        讓遊戲 popup 截圖與主流程截圖共享同一份 README.md。
        """
        self._step += 1
        filename = f"{self._step:03d}_{_sanitize(label)}.png"
        filepath = self.folder / filename
        target = page if page is not None else self.page
        # 截圖是觀察性用途，失敗不應阻塞測試主流程；written 記錄檔案是否真的寫出
        written = _write_screenshot(target, filepath)
        # full_page 本就不圈選，highlighted=None 表示 N/A（不列入圈選失敗統計）
        self._steps.append({
            "step": self._step,
            "label": label,
            "filename": filename,
            "kind": "full_page",
            "highlighted": None,
            "reason": "full_page",
            "match_count": None,
            "multi_match": False,
            "oversize": False,
            "written": written,
        })
        return filepath

    def generate_report(self) -> None:
        """將本次測試的操作步驟寫成 README.md（含圈選失敗 badge），
        並寫機器可讀 steps.json + 把圈選失敗步驟累加進 session 稽核累加器。"""
        if not self._steps:
            return

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # 統計截圖瑕疵步驟（圈選沒圈到 / 多命中 / 過大 / 截圖未寫出）
        # 涵蓋所有 step：full_page 沒寫出（written is False）也算瑕疵並計入
        fail_steps = [s for s in self._steps if _step_flawed(s)]

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
        ]
        lines.append(f"**截圖瑕疵步驟：** {len(fail_steps)}/{len(self._steps)} 步")
        lines += [
            "",
            "---",
            "",
            "## 操作步驟",
            "",
        ]

        # 每個步驟
        for s in self._steps:
            zh = _label_to_zh(s["label"])
            badge = ""
            notes: list[str] = []
            if s.get("kind") == "capture":
                if s.get("highlighted") is False:
                    badge = " ⚠️ 未圈到"
                    notes.append(f"> ⚠️ 圈選失敗（原因：{_REASON_ZH.get(s.get('reason'), s.get('reason'))}）— 此圖未標示目標元素")
                if s.get("multi_match"):
                    notes.append(f"> ⚠️ 命中 {s.get('match_count')} 個元素，只圈第一個（selector 需加 .first 或收斂）")
                if s.get("oversize"):
                    notes.append("> ⚠️ 目標框過大（幾乎覆蓋整個視窗），紅框無鑑別度")
            # written is False：截圖檔逾時未寫出（舊 steps.json 無此欄回 None ≠ False）
            missing = s.get("written") is False
            if missing:
                badge += " ⚠️ 截圖未寫出"
                notes.append("> ⚠️ 截圖檔未寫出（screenshot 逾時），此步驟無圖")
            lines.append(f"### 步驟 {s['step']:03d}｜{zh}{badge}")
            lines.append("")
            for n in notes:
                lines += [n, ""]
            # 未寫出者不嵌壞圖連結，避免 README 內出現破圖
            if not missing:
                lines += [
                    f"![步驟 {s['step']:03d} — {zh}]({s['filename']})",
                    "",
                ]

        report_path = self.folder / "README.md"
        report_path.write_text("\n".join(lines), encoding="utf-8")

        # 機器可讀 sidecar（供離線重掃 script 使用）
        steps_payload = {
            "test": self._test_name,
            "site": self._site_id,
            "category": self._category,
            "steps": self._steps,
        }
        try:
            (self.folder / "steps.json").write_text(
                json.dumps(steps_payload, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception:
            pass

        # 累加截圖瑕疵步驟進 session 稽核（sessionfinish 時彙整成報告）
        for s in fail_steps:
            _AUDIT_RECORDS.append({
                "site": self._site_id,
                "timestamp": self._timestamp,
                "category": self._category,
                "test": self._test_name,
                "step": s["step"],
                "label": s["label"],
                "reason": s.get("reason"),
                "match_count": s.get("match_count"),
                "multi_match": s.get("multi_match"),
                "oversize": s.get("oversize"),
                "written": s.get("written"),
                "path": str(self.folder / s["filename"]),
            })


def _highlight_and_screenshot(
    page: Page, locator: Locator, filepath: Path, label: str = ""
) -> dict:
    """
    自動捲入視野 → 取 bounding box → 判定是否真的圈得到 → 注入紅框（成功）
    或「未圈選」橫幅（失敗）→ 截圖 → 移除 overlay。

    回傳 status dict，供 capture() 記進 step metadata / 判定報告：
    {highlighted:bool, reason:str, match_count:int, multi_match:bool, oversize:bool, box:dict|None}

    契約：截圖純觀察性，任何步驟失敗都不得 raise、不得 fail 測試。
    """
    # 1) 多命中偵測
    try:
        match_count = locator.count()
    except Exception:
        match_count = -1  # 無法取得，不視為失敗訊號
    multi_match = match_count > 1

    target = locator.first

    if match_count == 0:
        written = _screenshot_with_optional_banner(page, filepath, "no_match", label)
        return {"highlighted": False, "reason": "no_match", "match_count": match_count,
                "multi_match": False, "oversize": False, "box": None, "written": written}

    # 2) 自動捲入視野（解 below-fold）。失敗不直接判定失敗——元素可能本就在視窗內，
    #    或如 RC width=0 sidebar / LT drawer 這類 scroll 無效者；一律吞例外續跑。
    scroll_error = False
    try:
        target.scroll_into_view_if_needed(timeout=_SCROLL_TIMEOUT_MS)
    except Exception:
        scroll_error = True

    # 3) 取 bounding_box
    box = None
    try:
        box = target.bounding_box(timeout=_BBOX_TIMEOUT_MS)
    except Exception:
        box = None

    # 4) 取視窗尺寸（CDP 下 viewport_size 可能為 None）
    vp = page.viewport_size
    if not vp:
        try:
            vp = page.evaluate("() => ({width: window.innerWidth, height: window.innerHeight})")
        except Exception:
            vp = None

    # 5) 分類 highlighted / reason
    reason = "ok"
    highlighted = True
    oversize = False
    if box is None:
        highlighted, reason = False, ("bbox_error" if scroll_error else "no_box")
    elif box["width"] * box["height"] == 0:
        highlighted, reason = False, "zero_area"
    elif vp and (
        box["x"] + box["width"] <= 0 or box["y"] + box["height"] <= 0
        or box["x"] >= vp["width"] or box["y"] >= vp["height"]
    ):
        # 與視窗矩形無交集 → 就算注入 fixed 紅框也在畫面外，誠實標成 offscreen
        highlighted, reason = False, "offscreen"
    else:
        if vp and (box["width"] * box["height"]) > vp["width"] * vp["height"] * _OVERSIZE_RATIO:
            oversize = True  # 框過大＝圈了等於沒圈（highlighted 仍 True，另立旗標）

    box_out = ({"x": box["x"], "y": box["y"], "w": box["width"], "h": box["height"]}
               if box else None)

    written = False
    try:
        if highlighted:
            _inject_highlight(page, box, label)
        else:
            _inject_banner(page, reason)
        # 截圖是觀察性用途，失敗不應阻塞測試主流程；written 記錄檔案是否真的寫出
        written = _write_screenshot(page, filepath)
    finally:
        _remove_overlay(page)

    return {"highlighted": highlighted, "reason": reason, "match_count": match_count,
            "multi_match": multi_match, "oversize": oversize, "box": box_out,
            "written": written}


def _inject_highlight(page: Page, box: dict, label: str) -> None:
    """在元素 bounding box 上注入紅框 + 標籤 overlay。"""
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


def _inject_banner(page: Page, reason: str) -> None:
    """圈選失敗時，在畫面正中央注入紅底白字「未圈選」橫幅（純前端注入，免依賴）。

    置中用全視窗 flex 容器（inset:0），**不用 transform、不設 pointer-events:none**：
    實測 headless 下，用 transform 置中或帶 pointer-events:none 的全視窗注入元素，在
    部分站點 desktop 版面不會 composite 進截圖（橫幅隱形）；改用 flex 容器可靠顯示。
    容器截圖後即由 _remove_overlay 移除，期間無任何點擊，故無需 pointer-events:none。
    """
    text = f"未圈選：{_REASON_ZH.get(reason, reason)}"
    try:
        page.evaluate(
            """(msg) => {
                const old = document.getElementById('__pw_highlight__');
                if (old) old.remove();

                const wrap = document.createElement('div');
                wrap.id = '__pw_highlight__';
                wrap.style.cssText = [
                    'position:fixed',
                    'inset:0',
                    'z-index:2147483647',
                    'display:flex',
                    'align-items:center',
                    'justify-content:center',
                ].join(';');

                const banner = document.createElement('div');
                banner.textContent = msg;
                banner.style.cssText = [
                    'background:rgba(255,51,51,0.95)',
                    'color:#fff',
                    'padding:10px 24px',
                    'border-radius:6px',
                    // 白框 + 深色陰影：即使壓在同色系（如紅色 hero）背景上也能辨識
                    'border:2px solid #fff',
                    'font:bold 16px/1.4 sans-serif',
                    'white-space:nowrap',
                    'box-shadow:0 2px 16px rgba(0,0,0,0.6)',
                ].join(';');
                wrap.appendChild(banner);

                document.body.appendChild(wrap);
            }""",
            text,
        )
    except Exception:
        pass


def _remove_overlay(page: Page) -> None:
    try:
        page.evaluate("""() => {
            const el = document.getElementById('__pw_highlight__');
            if (el) el.remove();
        }""")
    except Exception:
        pass


def _write_screenshot(target, filepath: Path) -> bool:
    """截圖寫檔，回傳是否成功。失敗先以 animations='disabled' retry 一次（凍結 CSS 動畫，
    緩解忙碌 SPA 首頁撞 timeout 的 transient），仍失敗回 False、不拋出。

    target 可為 Page 或另開分頁的 popup page，皆有 .screenshot()。
    """
    try:
        target.screenshot(path=str(filepath), timeout=_SCREENSHOT_TIMEOUT_MS)
        return True
    except Exception:
        pass
    try:
        target.screenshot(path=str(filepath), timeout=_SCREENSHOT_TIMEOUT_MS,
                          animations="disabled")
        return True
    except Exception:
        return False


def _screenshot_with_optional_banner(page: Page, filepath: Path, reason: str, label: str) -> bool:
    """no_match 等提早返回情境：注入橫幅 → 截圖 → 移除。回傳截圖是否寫出。"""
    try:
        _inject_banner(page, reason)
        return _write_screenshot(page, filepath)
    finally:
        _remove_overlay(page)


def _render_audit(records: list[dict]) -> tuple[str, str]:
    """把圈選失敗記錄 render 成 (markdown, json) 字串。
    write_highlight_audit()（線上）與 audit_highlights.py（離線重掃）共用。"""
    total_fail = len(records)
    tests = {(r["category"], r["test"]) for r in records}
    reason_dist: dict[str, int] = {}
    for r in records:
        # 截圖未寫出（連檔案都沒有）優先歸入獨立 bucket，比圈選原因更根本
        if r.get("written") is False:
            key = "not_written"
        else:
            key = r.get("reason") or ("multi_match" if r.get("multi_match") else
                                      "oversize" if r.get("oversize") else "?")
        reason_dist[key] = reason_dist.get(key, 0) + 1

    lines: list[str] = [
        "# 截圖圈選稽核報告",
        "",
        f"**截圖有瑕疵步驟：** {total_fail} 步，涉及 {len(tests)} 支測試",
        "",
        "**原因分佈：** " + (
            "、".join(f"{_REASON_ZH.get(k, k)}={v}" for k, v in sorted(reason_dist.items()))
            or "（無）"
        ),
        "",
        "| 分類 | test | 步驟 | label | 原因 | 命中數 | 檔案 |",
        "|------|------|------|-------|------|-------|------|",
    ]
    for r in sorted(records, key=lambda x: (x["category"], x["test"], x["step"])):
        tags = []
        if r.get("reason") in _FAIL_REASONS:
            tags.append(_REASON_ZH.get(r["reason"], r["reason"]))
        if r.get("multi_match"):
            tags.append("多命中")
        if r.get("oversize"):
            tags.append("框過大")
        if r.get("written") is False:
            tags.append("截圖未寫出")
        reason_txt = "／".join(tags) or "-"
        lines.append(
            f"| {r['category']} | {r['test']} | {r['step']:03d} | {r['label']} | "
            f"{reason_txt} | {r.get('match_count')} | {r.get('path', '')} |"
        )
    md = "\n".join(lines) + "\n"
    payload = json.dumps({"total": total_fail, "tests": len(tests),
                          "reason_dist": reason_dist, "records": records},
                         ensure_ascii=False, indent=2)
    return md, payload


def write_highlight_audit() -> None:
    """把 session 累加的圈選失敗記錄，依 (site, timestamp) 各寫一份稽核報告到
    screenshots/<site>/<timestamp>/_highlight_audit.md + .json。pytest_sessionfinish 呼叫。"""
    if not _AUDIT_RECORDS:
        return
    groups: dict[tuple[str, str], list[dict]] = {}
    for r in _AUDIT_RECORDS:
        groups.setdefault((r["site"], r["timestamp"]), []).append(r)
    for (site, ts), records in groups.items():
        folder = SCREENSHOTS_DIR / site / ts
        try:
            folder.mkdir(parents=True, exist_ok=True)
            md, payload = _render_audit(records)
            (folder / "_highlight_audit.md").write_text(md, encoding="utf-8")
            (folder / "_highlight_audit.json").write_text(payload, encoding="utf-8")
        except Exception:
            pass
