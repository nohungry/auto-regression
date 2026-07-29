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
# 通用警示：code 改了但完全沒同步任何共享 .md
warn_block() {
  local changed_code="$1"
  local exit_code="$2"
  cat >&2 <<EOF

⚠️  Docs sync check：程式碼有變動但無對應 .md 更新

變動的 code 檔案：
$(echo "$changed_code" | sed 's/^/  - /')

請依 CLAUDE.md 的「文檔維護對照表（code 變動 → 要同步的 doc）」確認該動哪份 doc，
並記得 root README.md 是第一公民（站台表 / 目錄樹 / 執行指令 / markers）。

確認不需要更新時的 override 方式：
  - commit message 加 sentinel：[skip-docs-check] 並附理由
  - 或 env var：SKIP_DOCS_CHECK=1

EOF
  exit "$exit_code"
}

# 特定規則警示：某類 code 變動「必須」同步指定 doc 卻沒同步
block_rule() {
  local label="$1"
  local required="$2"
  local exit_code="$3"
  cat >&2 <<EOF

⚠️  Docs sync check：$label

依 CLAUDE.md「文檔維護對照表」此類變動必須同步更新：
$(echo "$required" | sed 's/^/  - /')

確認不需要更新時的 override：commit message 加 [skip-docs-check] 並附理由，或 SKIP_DOCS_CHECK=1

EOF
  exit "$exit_code"
}

# CHANGED 內是否含某個確切檔名
changed_has() { echo "$CHANGED" | grep -qxF "$1"; }

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
  ADDED=$(git diff --cached --name-only --diff-filter=A)
  EXIT_CODE=2  # Claude PreToolUse hook：exit 2 = block + stderr
fi

# === CI 模式：對 PR 全變動 ===
if [ "$MODE" = "ci" ]; then
  # PR 全 commit 任一含 sentinel → 略過
  if git log "$BASE_SHA"..HEAD --pretty=format:%B | grep -q '\[skip-docs-check\]'; then
    exit 0
  fi
  CHANGED=$(git diff --name-only "$BASE_SHA"..HEAD)
  ADDED=$(git diff --name-only --diff-filter=A "$BASE_SHA"..HEAD)
  EXIT_CODE=1  # workflow fail
fi

# === 共用核心檢查 ===
# 1) Deterministic 硬規則：某類 code 變動「必須」同步特定 doc（對照 CLAUDE.md 文檔維護對照表最高訊號的兩列）
#    新前台站點：新增 pages/<id>/login_page.py（排除 pages/dashboard/<id>/... 多一層路徑）→ 必須同改 README + CLAUDE
if echo "$ADDED" | grep -qE '^pages/[^/]+/login_page\.py$'; then
  if ! { changed_has "README.md" && changed_has "CLAUDE.md"; }; then
    block_rule "偵測到新增前台站點，但未同步站台文檔" \
      "README.md（站台表 / 目錄樹 / 執行指令 / markers 表）
CLAUDE.md（Architecture 樹 / 站點清單 / factory 段）" \
      "$EXIT_CODE"
  fi
fi

#    依賴雙軌同步（uv 雙軌制）：pyproject.toml / uv.lock 變動 → requirements.txt 必須同步 re-export
if { changed_has "pyproject.toml" || changed_has "uv.lock"; } && ! changed_has "requirements.txt"; then
  block_rule "依賴（pyproject.toml / uv.lock）有變動，但 requirements.txt 未同步 re-export" \
    "requirements.txt（執行：uv export --no-hashes -o requirements.txt 後重新 git add）" \
    "$EXIT_CODE"
fi

#    反向：requirements.txt 是 uv export 產物，禁止單獨手改（須經 pyproject.toml → uv lock → uv export）
if changed_has "requirements.txt" && ! { changed_has "pyproject.toml" || changed_has "uv.lock"; }; then
  block_rule "requirements.txt 單獨變動（它是 uv export 產物，不可手改）" \
    "pyproject.toml（依賴 source of truth，改這裡）
uv.lock（執行 uv lock 產生）
requirements.txt（執行 uv export --no-hashes -o requirements.txt 重新產生）" \
    "$EXIT_CODE"
fi

#    marker 變動：pytest.ini 在 diff → 必須同改 README + CLAUDE（兩處都列 marker）
if changed_has "pytest.ini"; then
  if ! { changed_has "README.md" && changed_has "CLAUDE.md"; }; then
    block_rule "pytest.ini（marker）有變動，但未同步 marker 文檔" \
      "README.md（測試分級與 Markers 表）
CLAUDE.md（Markers 清單）" \
      "$EXIT_CODE"
  fi
fi

# 2) 通用 fallback：code 改了但完全沒同步任何「共享」.md（dev-notes 個人筆記不算數）
CHANGED_CODE=$(echo "$CHANGED" | grep -E "$CODE_RE" || true)
CHANGED_DOCS=$(echo "$CHANGED" | grep -E "$DOC_RE" | grep -vE '^dev-notes/' || true)

if [ -n "$CHANGED_CODE" ] && [ -z "$CHANGED_DOCS" ]; then
  warn_block "$CHANGED_CODE" "$EXIT_CODE"
fi

exit 0
