# CI/CD 操作指南

GitHub Actions 自動跑這個 repo 的測試。當前 3 個 workflow：

| Workflow | 觸發 | 跑什麼 | 預估時長 |
|---|---|---|---|
| `p0.yml` | PR（**draft 不跑**，轉 ready 才跑）/ push to main / daily cron / 手動 | 8 站 P0 smoke matrix（rc/lt/re/rd/qw/lg/lu/rf） | ~3 分（8 job 並行） |
| `full-regression.yml` | weekly cron（週一） / 手動 | 8 站全套（P0 + feature） | ~17 分（8 job 並行） |
| `docs-sync-check.yml` | PR | PR 靜態檢查集（三 job）：code 變動是否同步 docs + `tests/` factory import 守門 + `requirements.txt` 與 `uv.lock` export 同步 | < 30 秒 |

## Cron 時段（台灣時區）

| Workflow | Cron (UTC) | 台灣時間 |
|---|---|---|
| `p0.yml` daily | `0 1 * * *` | 每天 09:00 |
| `full-regression.yml` weekly | `0 0 * * 1` | 每週一 08:00 |

注：GitHub cron 可能延遲幾分鐘到 1 小時，負載高時甚至 skip 該 schedule（無補跑機制）。

## Secrets 清單

`https://github.com/<owner>/<repo>/settings/secrets/actions` 設定，CI 實際使用 24 個（8 站 × 3）：

| Site | Secrets |
|---|---|
| RC | `SITE_RC_URL` / `SITE_RC_USERNAME` / `SITE_RC_PASSWORD` |
| LT | `SITE_LT_URL` / `SITE_LT_USERNAME` / `SITE_LT_PASSWORD` |
| RE | `SITE_RE_URL` / `SITE_RE_USERNAME` / `SITE_RE_PASSWORD` |
| RD | `SITE_RD_URL` / `SITE_RD_USERNAME` / `SITE_RD_PASSWORD` |
| QW | `SITE_QW_URL` / `SITE_QW_USERNAME` / `SITE_QW_PASSWORD` |
| LG | `SITE_LG_URL` / `SITE_LG_USERNAME` / `SITE_LG_PASSWORD` |
| LU | `SITE_LU_URL` / `SITE_LU_USERNAME` / `SITE_LU_PASSWORD` |
| RF | `SITE_RF_URL` / `SITE_RF_USERNAME` / `SITE_RF_PASSWORD` |

> **已退役站點**：KS 於 2026-07 永久下架。2026-08-05 已完成清理——移出兩個 workflow 的 matrix 與 env、刪除 POM / 測試 / registry / marker，`SITE_KS_URL` / `SITE_KS_USERNAME` / `SITE_KS_PASSWORD` 三個 GitHub secret 亦已刪除。歷史程式碼見 git 歷史。

**可選 secret**：`SLACK_WEBHOOK` — Slack Incoming Webhook URL。設了之後自動推通知到該頻道（含 run 連結 + 跨站聚合摘要）：
- **排程跑（不論成敗都推，當定時報）**：P0 daily（每日 09:00）→ **每日報**；full-regression weekly（每週一 08:00）→ **每週報**。
- **手動觸發（workflow_dispatch）**：不論成敗都推（方便隨時要一份摘要 / 驗證通知）。
- **PR / push**：**僅失敗才推**（成功不吵）。
- **未設則自動略過**（不影響 CI）。

設定方式：Slack 建 App → 啟用 Incoming Webhooks → Add to Workspace 選頻道 → 拿 webhook URL → `gh secret set SLACK_WEBHOOK`（貼上 URL）。

### 用 `gh` CLI 從本機 .env 一次設好

```bash
for site in RC LT RE RD QW LG LU RF; do
  for k in URL USERNAME PASSWORD; do
    grep "^SITE_${site}_${k}=" .env | cut -d= -f2- | gh secret set "SITE_${site}_${k}"
  done
done
```

值直接從本機 `.env` 讀，不會 echo 在 terminal。

## Concurrency lock

| Lock group | 用途 |
|---|---|
| `p0-${{ github.ref }}` | 同 PR 重複 push 取消上一次 |
| `full-regression-${{ github.ref }}` | 同 ref 重複手動觸發取消上一次 |
| `<site>-account` | 同 site 帳號不能並行（避免互踢 session）；p0.yml + full-regression.yml 共用同 group |

不同 site 不同帳號 → matrix 8 job 可並行。

## 看 workflow run

進 `https://github.com/<owner>/<repo>/actions` → 點該 run。

run 頁面看得到：
- 各 job ✅/❌
- 每 step 完整 log
- **跨站聚合成績單**（👉 一眼看完全站，建議優先看）：`aggregate-summary` job 在所有 site 跑完後，把 8 站 JUnit 聚合成**單一總覽表**（`Site | Passed | Failed | Error | Skipped | 🔁 Flaky | Duration` + 合計）+ **失敗測試總清單（按站分組）** + **🔁 Flaky 清單（重跑後才通過，按站分組）**，寫到該 run 的總 Step Summary。不用逐一點 8 個 site 的 Job Summary。
  - 機制：各 site job upload `junit-<site>` artifact（含 `junit/<site>.xml` + `junit/<site>-flaky.json` flaky sidecar）→ `aggregate-summary` job（`needs` matrix、`if: always()`）download 全部 → 跑 `.github/scripts/aggregate_test_results.py` 寫 `$GITHUB_STEP_SUMMARY`。
  - 全綠時顯示「✅ 全 8 站全數通過 🎉」；有失敗時列出哪站哪些 test。
  - **🔁 Flaky 欄／清單**：CI 用 `--reruns 1`，`conftest.py` 的 `pytest_runtest_logreport`/`pytest_sessionfinish` hook 把「**重跑後才通過**」的 test（＝本次 flaky，綠燈但值得追）寫成 `junit/<site>-flaky.json` sidecar，聚合後顯示。真失敗（重跑仍 fail）不算 flaky、照常計入 Failed。
- **各站 Job Summary**：個別 site 的 pytest 結果 markdown 表格（pass/fail/skip + 失敗 test 名單），看單站細節用。
- **Artifacts**（頁面最下方）：
  - `report-html-<site>.zip` / `full-regression-report-<site>.zip`：自包式 HTML 報告（保留 30 天）
  - `failure-screenshots-<site>.zip`（**只有失敗時上傳**，保留 14 天）：紅框截圖 + 自動生成 README.md
  - `junit-<site>.zip`：JUnit XML + `<site>-flaky.json`（聚合成績單／flaky 欄的原始資料）

### 截圖圈選稽核（`.github/scripts/audit_highlights.py`）

跑測試時 `conftest.py` `pytest_sessionfinish` 會呼叫 `write_highlight_audit()`，把「呼叫了 `sh.capture` 卻沒真的圈到元素」的步驟彙整成 `screenshots/<site>/<ts>/_highlight_audit.md`/`.json`（取代人工逐張翻圖找失準截圖）。`audit_highlights.py <dir>` 可離線重掃既有 `steps.json` 重建同樣報告（不必重跑），`--fail-threshold N` 在失敗步驟數超標時回傳非 0 exit code，供未來接入 CI 門檻。詳見 CLAUDE.md「Screenshot System → 圈選判定」。

## 手動觸發

任一 workflow 的「Actions」頁面右上有「Run workflow」按鈕。

或用 `gh` CLI：

```bash
gh workflow run p0.yml                  # P0 smoke
gh workflow run full-regression.yml     # 全套 regression
gh workflow run p0.yml --ref <branch>   # 指定 branch（workflow 須在 default branch）
```

## 模擬 CI 本機跑

```bash
CI=true .venv/bin/pytest tests/rc/test_p0_smoke.py
```

`CI=true` 觸發 `conftest.py` 的 `_is_ci()` 分支，走 headless chromium（不走 CDP / Windows Chrome）。預設 `HEADLESS=true`，要 debug 看畫面就 `HEADLESS=false`。

## Debug 失敗

| 現象 | 怎查 |
|---|---|
| 某 step fail | 點 step 看 log；常見：`Run <site> P0 smoke` 內可見 pytest output / traceback |
| Test fail 但本機過 | 下載 `failure-screenshots-<site>.zip`，看 README.md 與紅框截圖比對本機行為 |
| Workflow 沒觸發 | 確認 trigger 規則（如 `pull_request: branches: [main]` 只認對 main 的 PR） |
| **Draft PR 沒跑 p0** | **by design**：draft = 施工中訊號（雙人協作協定），不跑 8 站 smoke 以免佔用共用測試帳號與本地 CDP 互踢；PR 轉 ready for review 即觸發 |
| Cron 沒跑 | GitHub 負載高時可能 skip；隔天看 / 改 cron 加多個時段 |
| Secret 缺 | `gh secret list` 確認；或 step log 會出現 `SITE_X_PASSWORD: ${{ secrets.SITE_X_PASSWORD }}` 變空字串 → 測試 fail 在 login |

## Docs sync check（hook + CI 雙保險）

每次 commit / PR 自動檢查「程式碼變動是否同步更新 docs」。

### 機制

- **L2 Hook**（`.claude/settings.json` + `.github/scripts/check-docs-sync.sh`）：Claude Code session 內，跑 `git commit` 之前 block，stderr 列出建議重看的 docs
- **L4 CI**（`.github/workflows/docs-sync-check.yml`）：PR 時相同檢查跑一次，違規 → job fail / PR check 紅
- 兩者**共用同一份 script**（`.github/scripts/check-docs-sync.sh`），模式靠 stdin / arg 差異判斷

### 哪些 code 路徑會觸發

```
conftest.py
pages/
utils/
tests/*/conftest.py
.github/workflows/*.yml
.claude/settings.json
```

### Override

確認**不**需要更新 docs 時：

| 方式 | 用途 |
|---|---|
| commit message 加 sentinel `[skip-docs-check]` 並附理由 | 單次 commit 略過 |
| 設環境變數 `SKIP_DOCS_CHECK=1` | session 內所有 commit 略過 |

範例：

```bash
git commit -m "fix(test): typo in test docstring [skip-docs-check] 純註解錯字無需動 docs"
```

## Factory import guard（D-001 / D-002 守門）

`tests/` 內禁止直接 import 站點 POM，必須走 factory（`docs/decisions.md` D-001 前台 / D-002 後台，守門機制本身為 D-023）。2026-08 清理時實測仍有 62 行 / 42 檔違規，證明純靠紀律與 code review 已失效。

### 機制

- **Hook**（`.claude/settings.json` + `.github/scripts/check-factory-import.sh`）：`git commit` 前檢 `git diff --cached` 的 `tests/**/*.py`，違規 exit 2 block
- **CI**（`docs-sync-check.yml` 的 `factory-import-check` job）：掃 `tests/` **全樹**（非 diff），違規 exit 1 → PR check 紅
- 兩者共用同一份 script，模式靠 stdin / arg 差異判斷（同 `check-docs-sync.sh` 骨架）

> hook 檢 staged、CI 掃全樹是刻意的分工：hook 要快且不被存量違規卡住；CI 掃全樹才抓得到「搬檔／改名」這種 diff 看不出來的逃逸。

### 判定規則（例外法）

掃 `tests/` 內所有 `from pages.` 行，**僅字面放行**兩者：

```
from pages.factory import ...
from pages.dashboard.factory import ...
```

其餘一律違規。這個寫法**不硬編站點清單** → 新增站點零維護，且同時涵蓋前台（`pages.<site>.x`）、後台（`pages.dashboard.<site>.x`）、以及 `from pages.rc import login_page` 這種單段逃逸型。

> 不採「從 factory registry 動態推導站名」：會漏掉後台 D-002 型違規，且 bash 讀 python registry 會讓 hook 變慢。

### 正確寫法

```python
from pages.factory import get_login_page_class, get_home_page_class

LoginPage = get_login_page_class("rc")
HomePage = get_home_page_class("rc")
```

賦值必須早於該檔任何 module-level 使用點（例如函式簽名的型別註記），否則 `NameError`。

### Override

```bash
git commit -m "test(x): ... [skip-factory-check] <理由>"
# 或
SKIP_FACTORY_CHECK=1 git commit -m "..."
```

## uv requirements export sync（依賴雙軌守門）

依賴管理採 uv 雙軌制（`docs/decisions.md` D-022）：`pyproject.toml` + `uv.lock` 為 source of truth，`requirements.txt` 為 `uv export` 鎖定版產物。守門同樣 hook + CI 雙保險：

- **Hook**（`check-docs-sync.sh` deterministic 規則）：staged 含 `pyproject.toml`/`uv.lock` 但沒動 `requirements.txt` → block（提示跑 `uv export --no-hashes -o requirements.txt`）；反向單獨改 `requirements.txt` 也 block（禁手改產物）
- **CI**（`docs-sync-check.yml` 的 `uv-requirements-sync` job）：裝 uv → `uv export --frozen --no-hashes` 與 `requirements.txt` diff（忽略註解行）；`--frozen` 使「改了 pyproject 沒跑 `uv lock`」也直接紅

### 想升級成 hard block（PR merge 強制要求）

repo Settings → Branches → main → Add branch protection rule → Require status checks → 勾 `Docs Sync Check`。

當前未設 required check，PR 紅但仍可 merge（軟提醒）。
