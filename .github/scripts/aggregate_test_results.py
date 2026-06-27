#!/usr/bin/env python3
"""
跨站聚合 CI 成績單：讀多份 pytest JUnit XML → 產出 markdown 總覽表 + 失敗清單。

用途：CI matrix（9 站各自一份 junit/<site>.xml）跑完後，由 aggregate-summary job
呼叫本 script，把輸出 append 進 $GITHUB_STEP_SUMMARY，讓 run 頁面一眼看完全站成績。

純 stdlib（xml.etree），CI 不需額外安裝。

用法：
    python aggregate_test_results.py --junit-dir junit --title "P0 Smoke" >> "$GITHUB_STEP_SUMMARY"

site 名稱取自 JUnit 檔名 stem（junit/rc.xml → rc）；遞迴 glob 容忍 download-artifact 的路徑巢狀。
"""

import argparse
import glob
import os
import xml.etree.ElementTree as ET


def _fmt_duration(seconds: float) -> str:
    s = int(round(seconds))
    if s < 60:
        return f"{s}s"
    return f"{s // 60}m {s % 60:02d}s"


def _iter_testsuites(root):
    """root 可能是 <testsuites>（含多個 testsuite）或單一 <testsuite>。"""
    if root.tag == "testsuite":
        yield root
    else:
        for ts in root.findall("testsuite"):
            yield ts


def parse_one(path):
    """解析單一 JUnit XML，回傳 site 統計 dict。"""
    site = os.path.splitext(os.path.basename(path))[0]
    tests = failures = errors = skipped = 0
    duration = 0.0
    failed_names = []
    try:
        root = ET.parse(path).getroot()
    except ET.ParseError as e:
        return {"site": site, "parse_error": str(e), "tests": 0, "failures": 0,
                "errors": 0, "skipped": 0, "passed": 0, "duration": 0.0, "failed_names": []}

    for ts in _iter_testsuites(root):
        tests += int(ts.get("tests", 0))
        failures += int(ts.get("failures", 0))
        errors += int(ts.get("errors", 0))
        skipped += int(ts.get("skipped", 0))
        duration += float(ts.get("time", 0) or 0)
        for tc in ts.findall("testcase"):
            if tc.find("failure") is not None or tc.find("error") is not None:
                cls = (tc.get("classname") or "").split(".")[-1]
                name = tc.get("name") or "?"
                failed_names.append(f"{cls}::{name}" if cls else name)

    passed = max(tests - failures - errors - skipped, 0)
    return {"site": site, "tests": tests, "failures": failures, "errors": errors,
            "skipped": skipped, "passed": passed, "duration": duration,
            "failed_names": failed_names, "parse_error": None}


def build_markdown(stats, title):
    lines = []
    lines.append(f"## 🧪 {title} — 跨站聚合成績單\n")
    lines.append("| Site | ✅ Passed | ❌ Failed | ⚠️ Error | ⏭ Skipped | ⏱ Duration |")
    lines.append("|------|----------:|----------:|---------:|----------:|-----------:|")

    tot = {"passed": 0, "failures": 0, "errors": 0, "skipped": 0, "duration": 0.0}
    any_fail = False
    for st in stats:
        if st["parse_error"]:
            lines.append(f"| {st['site']} | — | — | — | — | ⚠️ XML 解析失敗 |")
            any_fail = True
            continue
        lines.append(
            f"| {st['site']} | {st['passed']} | {st['failures']} | {st['errors']} "
            f"| {st['skipped']} | {_fmt_duration(st['duration'])} |"
        )
        for k in tot:
            tot[k] += st[k] if k != "duration" else st["duration"]
        if st["failures"] or st["errors"]:
            any_fail = True

    lines.append(
        f"| **合計** | **{tot['passed']}** | **{tot['failures']}** | **{tot['errors']}** "
        f"| **{tot['skipped']}** | **{_fmt_duration(tot['duration'])}** |"
    )
    lines.append("")

    # 失敗清單（按站分組）
    fail_blocks = []
    for st in stats:
        if st["failed_names"]:
            names = ", ".join(f"`{n}`" for n in st["failed_names"])
            fail_blocks.append(f"- **{st['site']}**（{len(st['failed_names'])}）：{names}")

    if fail_blocks:
        lines.append("### ❌ 失敗測試（按站分組）\n")
        lines.extend(fail_blocks)
    elif any_fail:
        lines.append("> ⚠️ 有站別 XML 解析失敗或非測試錯誤，請查各站 job log。")
    else:
        lines.append("### ✅ 全 9 站全數通過 🎉")
    lines.append("")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--junit-dir", default="junit", help="JUnit XML 目錄（遞迴 glob *.xml）")
    ap.add_argument("--title", default="Test Results", help="標題（如 P0 Smoke / Full Regression）")
    args = ap.parse_args()

    paths = sorted(glob.glob(os.path.join(args.junit_dir, "**", "*.xml"), recursive=True))
    if not paths:
        print(f"## 🧪 {args.title} — 跨站聚合成績單\n\n> ⚠️ 找不到任何 JUnit XML（{args.junit_dir}/**/*.xml）。")
        return

    stats = [parse_one(p) for p in paths]
    print(build_markdown(stats, args.title))


if __name__ == "__main__":
    main()
