#!/usr/bin/env bash
# Factory import guard（docs/decisions.md D-001 / D-002 / D-023）
#
# tests/ 內禁止直接 import 站點 POM，必須走 factory。判定採**例外法**：
#   掃 tests/ 內所有 `from pages.` 行，僅字面放行
#     - from pages.factory import ...
#     - from pages.dashboard.factory import ...
#   其餘一律違規。不硬編站點清單 → 新增站點零維護，且同時涵蓋
#   前台（pages.<site>.x）與後台（pages.dashboard.<site>.x）兩型，
#   以及 `from pages.rc import login_page` 這種單段逃逸寫法。
#
# 兩種模式（單一檔案共用，骨架對齊 check-docs-sync.sh）：
#   Hook 模式（無 arg，stdin 讀 PreToolUse JSON）：僅 Bash + `git commit` 時作用，
#     檢查 staged 的 tests/*.py → 違規 exit 2（block + stderr）
#   CI 模式（傳任意 arg）：掃 tests/ 全樹（非 diff，可抓搬檔／改名逃逸）→ 違規 exit 1
#
# Override：commit message 含 [skip-factory-check]，或 env SKIP_FACTORY_CHECK=1

set -euo pipefail

# BAD_RE 套在檔案內容上（行首錨定）；ALLOW_RE 套在 grep -n 的 `檔名:行號:內容`
# 組合行上，故錨點必須是 `:行號:` 而非 `^`（否則 allowlist 永遠對不上）。
BAD_RE='^[[:space:]]*from[[:space:]]+pages\.'
ALLOW_RE=':[0-9]+:[[:space:]]*from[[:space:]]+pages\.(dashboard\.)?factory[[:space:]]+import'

if [ "${SKIP_FACTORY_CHECK:-0}" = "1" ]; then
  exit 0
fi

if [ -n "${1:-}" ]; then
  MODE=ci
  EXIT_CODE=1
else
  MODE=hook
  EXIT_CODE=2
  STDIN_INPUT="$(cat)"
  TOOL_NAME=$(echo "$STDIN_INPUT" | python3 -c "import json,sys; print(json.load(sys.stdin).get('tool_name',''))" 2>/dev/null || echo "")
  COMMAND=$(echo "$STDIN_INPUT" | python3 -c "import json,sys; print(json.load(sys.stdin).get('tool_input',{}).get('command',''))" 2>/dev/null || echo "")
  [ "$TOOL_NAME" != "Bash" ] && exit 0
  echo "$COMMAND" | grep -q "git commit" || exit 0
  echo "$COMMAND" | grep -q '\[skip-factory-check\]' && exit 0
fi

if [ "$MODE" = "hook" ]; then
  FILES=$(git diff --cached --name-only --diff-filter=ACMR | grep -E '^tests/.*\.py$' || true)
else
  FILES=$(find tests -name '*.py' -type f 2>/dev/null | sort)
fi
[ -z "$FILES" ] && exit 0

VIOLATIONS=$(echo "$FILES" | xargs -r grep -nE "$BAD_RE" 2>/dev/null | grep -vE "$ALLOW_RE" || true)
[ -z "$VIOLATIONS" ] && exit 0

cat >&2 <<EOF

⛔  Factory import guard（docs/decisions.md D-001 / D-002 / D-023）

tests/ 內禁止直接 import 站點 POM，必須走 factory：

  ❌ from pages.rc.home_page import HomePage
  ✅ from pages.factory import get_home_page_class
     HomePage = get_home_page_class("rc")

  ❌ from pages.dashboard.rc.management_page import ManagementPage
  ✅ from pages.dashboard.factory import get_dashboard_management_page_class

  賦值必須早於該檔任何 module-level 使用點（例如函式簽名的型別註記），否則 NameError。

違規位置：
$(echo "$VIOLATIONS" | sed 's/^/  /')

確認為例外時的 override：commit message 加 [skip-factory-check] 並附理由，或 SKIP_FACTORY_CHECK=1

EOF
exit "$EXIT_CODE"
