#!/usr/bin/env bash
# Docs sync check：commit / PR 變動 code 但無對應 .md 更新時警示。
#
# 兩種使用模式（單一檔案共用）：
#   Hook 模式（Claude Code PreToolUse 用，無 arg）：
#     從 stdin 讀 JSON（{"tool_name", "tool_input": {"command"}}）
#     僅當 tool=Bash 且 command 含 `git commit` 才作用
#     檢查 git diff --cached 的 staged 檔案
#     違規 → exit 2（block + stderr 給 Claude 看）
#
#   CI 模式（GH Actions PR workflow 用，傳 base SHA）：
#     檢查 git diff <BASE>..HEAD 的 PR 全變動
#     違規 → exit 1（job fail / PR check 紅）
#
# Override（兩模式皆生效）：
#   1. commit message 含 `[skip-docs-check]` → 略過
#   2. env var `SKIP_DOCS_CHECK=1` → 略過

set -euo pipefail

# === 設定（fact-only，要改 mapping 直接動下面）===
# 視為「程式碼」的路徑 regex（任何 match 都會觸發檢查）
CODE_RE='^(conftest\.py|pages/.*|utils/.*|tests/[^/]+/conftest\.py|\.github/workflows/[^/]+\.yml|\.github/scripts/.*|\.claude/settings\.json)$'

# 視為「文件」的路徑 regex
DOC_RE='\.md$'

# === Helpers ===
warn_block() {
  local changed_code="$1"
  local exit_code="$2"
  cat >&2 <<EOF

⚠️  Docs sync check：程式碼有變動但無對應 .md 更新

變動的 code 檔案：
$(echo "$changed_code" | sed 's/^/  - /')

請重新確認下列 docs 是否需要同步更新：
  - CLAUDE.md（架構 / 慣例）
  - docs/cicd.md（CI/CD 觸發規則 / 操作）
  - docs/i18n_locale_text_reference.md（LT selector / i18n 對照表）
  - docs/testing-strategy.md（測試策略）
  - docs/README.md（文件索引）

確認不需要更新時的 override 方式：
  - commit message 加 sentinel：[skip-docs-check] 並附理由
  - 或 env var：SKIP_DOCS_CHECK=1

EOF
  exit "$exit_code"
}

# === 模式判定 ===
if [ -n "${1:-}" ]; then
  MODE="ci"
  BASE_SHA="$1"
else
  MODE="hook"
fi

# === Override：env var ===
if [ "${SKIP_DOCS_CHECK:-}" = "1" ]; then
  exit 0
fi

# === Hook 模式：從 stdin 解析 JSON ===
if [ "$MODE" = "hook" ]; then
  STDIN_INPUT="$(cat)"

  TOOL_NAME=$(echo "$STDIN_INPUT" | python3 -c "import json,sys; print(json.load(sys.stdin).get('tool_name', ''))" 2>/dev/null || echo "")
  COMMAND=$(echo "$STDIN_INPUT" | python3 -c "import json,sys; print(json.load(sys.stdin).get('tool_input', {}).get('command', ''))" 2>/dev/null || echo "")

  # 不是 Bash tool / 不是 git commit → 立即放行
  if [ "$TOOL_NAME" != "Bash" ] || ! echo "$COMMAND" | grep -q "git commit"; then
    exit 0
  fi

  # commit message 含 sentinel → 略過
  if echo "$COMMAND" | grep -q '\[skip-docs-check\]'; then
    exit 0
  fi

  CHANGED=$(git diff --cached --name-only)
  EXIT_CODE=2  # Claude PreToolUse hook：exit 2 = block + stderr
fi

# === CI 模式：對 PR 全變動 ===
if [ "$MODE" = "ci" ]; then
  # PR 全 commit 任一含 sentinel → 略過
  if git log "$BASE_SHA"..HEAD --pretty=format:%B | grep -q '\[skip-docs-check\]'; then
    exit 0
  fi
  CHANGED=$(git diff --name-only "$BASE_SHA"..HEAD)
  EXIT_CODE=1  # workflow fail
fi

# === 共用核心檢查 ===
CHANGED_CODE=$(echo "$CHANGED" | grep -E "$CODE_RE" || true)
CHANGED_DOCS=$(echo "$CHANGED" | grep -E "$DOC_RE" || true)

if [ -n "$CHANGED_CODE" ] && [ -z "$CHANGED_DOCS" ]; then
  warn_block "$CHANGED_CODE" "$EXIT_CODE"
fi

exit 0
