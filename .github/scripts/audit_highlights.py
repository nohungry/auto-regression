#!/usr/bin/env python3
"""離線重掃截圖圈選稽核報告。

純讀既有 screenshots/**/steps.json（由 ScreenshotHelper.generate_report 產出），
重建 _highlight_audit.md / .json —— 可對「歷史已產出的 run」離線稽核，不必重跑測試。

與線上 write_highlight_audit() 共用同一 render 函式（utils.screenshot_helper._render_audit），
確保線上／離線報告格式一致。

用法：
    python .github/scripts/audit_highlights.py screenshots/rc/20260702_2334
    python .github/scripts/audit_highlights.py screenshots/           # 遞迴掃全部 run
    python .github/scripts/audit_highlights.py screenshots/rc --fail-threshold 5

離開碼：--fail-threshold N 時，若圈選失敗步驟數 >= N 回傳 1（供 CI 門檻）；否則 0。
"""
import argparse
import json
import sys
from pathlib import Path

# 讓 script 能 import repo 內的 utils（script 位於 .github/scripts/）
_REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_REPO_ROOT))

from utils.screenshot_helper import _render_audit, _step_flawed  # noqa: E402


def _collect_records(root: Path) -> list[dict]:
    """掃 root 下所有 steps.json，抽出圈選有瑕疵的 capture 步驟為稽核記錄。"""
    records: list[dict] = []
    for steps_file in root.rglob("steps.json"):
        try:
            data = json.loads(steps_file.read_text(encoding="utf-8"))
        except Exception:
            continue
        test_dir = steps_file.parent
        # steps.json 位於 screenshots/<site>/<ts>/<category>/<test>/
        try:
            site = data.get("site") or test_dir.parents[2].name
            timestamp = test_dir.parents[1].name
        except IndexError:
            site, timestamp = data.get("site", "unknown"), "unknown"
        for s in data.get("steps", []):
            if s.get("kind") != "capture" or not _step_flawed(s):
                continue
            records.append({
                "site": site,
                "timestamp": timestamp,
                "category": data.get("category", ""),
                "test": data.get("test", test_dir.name),
                "step": s["step"],
                "label": s.get("label", ""),
                "reason": s.get("reason"),
                "match_count": s.get("match_count"),
                "multi_match": s.get("multi_match"),
                "oversize": s.get("oversize"),
                "path": str(test_dir / s.get("filename", "")),
            })
    return records


def main() -> int:
    ap = argparse.ArgumentParser(description="離線重掃截圖圈選稽核報告")
    ap.add_argument("root", help="要掃描的資料夾（screenshots/ 或某個 run 目錄）")
    ap.add_argument("--fail-threshold", type=int, default=None,
                    help="圈選失敗步驟數 >= 此值則回傳非 0 exit code（CI 門檻用）")
    ap.add_argument("--out", default=None,
                    help="報告輸出目錄（預設寫回被掃描的 root）")
    args = ap.parse_args()

    root = Path(args.root)
    if not root.exists():
        print(f"路徑不存在：{root}", file=sys.stderr)
        return 2

    records = _collect_records(root)
    md, payload = _render_audit(records)

    out_dir = Path(args.out) if args.out else root
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "_highlight_audit.md").write_text(md, encoding="utf-8")
    (out_dir / "_highlight_audit.json").write_text(payload, encoding="utf-8")

    total = len(records)
    print(f"掃描 {root} → 圈選有瑕疵步驟 {total} 步；報告寫入 {out_dir}/_highlight_audit.md")

    if args.fail_threshold is not None and total >= args.fail_threshold:
        print(f"⚠️ 失敗步驟 {total} >= 門檻 {args.fail_threshold}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
