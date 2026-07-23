#!/usr/bin/env bash
# Commit message style guard (Claude Code PreToolUse hook).
#
# Enforced on the commit subject (first -m argument's first line):
#   1. Conventional format: type(scope): summary  (scope optional)
#      types: feat|fix|test|chore|docs|refactor|ci|perf|revert|wip
#   2. English only — no CJK characters in the subject
#   3. Length <= 72 chars
#
# Details / rationale / [skip-docs-check] reason belong in the body
# (second -m argument), which is NOT length- or language-checked.
#
# Best-effort: if the message cannot be parsed from the command string
# (heredoc, -F file, interactive), the hook warns to stderr but allows.
#
# Override: env var SKIP_COMMIT_MSG_CHECK=1

set -euo pipefail

[ "${SKIP_COMMIT_MSG_CHECK:-0}" = "1" ] && exit 0

INPUT="$(cat)"

python3 - "$INPUT" <<'PYEOF'
import json, re, shlex, sys

raw = sys.argv[1]
try:
    data = json.loads(raw)
except Exception:
    sys.exit(0)

if data.get("tool_name") != "Bash":
    sys.exit(0)
cmd = (data.get("tool_input") or {}).get("command", "")
if not re.search(r"\bgit\s+commit\b", cmd):
    sys.exit(0)

# Extract first -m argument (the subject paragraph).
try:
    tokens = shlex.split(cmd)
except ValueError:
    print("check-commit-msg: cannot parse command (quoting); style not verified — "
          "keep subject English, type(scope): summary, <=72 chars", file=sys.stderr)
    sys.exit(0)

msg = None
for i, t in enumerate(tokens):
    if t == "-m" and i + 1 < len(tokens):
        msg = tokens[i + 1]
        break
    if t.startswith("-m") and len(t) > 2:
        msg = t[2:]
        break
if msg is None:
    # amend --no-edit, -F, heredoc etc. — best-effort pass
    sys.exit(0)

subject = msg.splitlines()[0].strip()
errors = []

if re.search(r"[　-〿㐀-鿿豈-﫿＀-￯]", subject):
    errors.append("subject contains CJK/full-width chars — write the subject in English "
                  "(Chinese detail goes to the PR body / second -m)")

if len(subject) > 72:
    errors.append(f"subject is {len(subject)} chars (max 72) — move detail to the body (second -m)")

if not re.match(r"^(feat|fix|test|chore|docs|refactor|ci|perf|revert|wip)(\([a-z0-9,/_-]+\))?: \S", subject):
    errors.append("subject must match `type(scope): summary` "
                  "(types: feat|fix|test|chore|docs|refactor|ci|perf|revert|wip)")

if errors:
    print("commit message style check FAILED (D-021):", file=sys.stderr)
    for e in errors:
        print(f"  - {e}", file=sys.stderr)
    print("example:\n  git commit -m 'test(lu): add wallet entry tests' "
          "-m '[skip-docs-check] test-only change; probe notes in PR #160'", file=sys.stderr)
    sys.exit(2)
sys.exit(0)
PYEOF
