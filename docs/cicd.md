# CI/CD 操作指南

GitHub Actions 自動跑這個 repo 的測試。當前 3 個 workflow：

| Workflow | 觸發 | 跑什麼 | 預估時長 |
|---|---|---|---|
| `p0.yml` | PR / push to main / daily cron / 手動 | 4 站 P0 smoke matrix | ~3 分（4 job 並行） |
| `full-regression.yml` | weekly cron（週一） / 手動 | 4 站全套（P0 + feature） | ~17 分（4 job 並行） |
| `docs-sync-check.yml` | PR | code 變動是否同步 docs | < 30 秒 |

## Cron 時段（台灣時區）

| Workflow | Cron (UTC) | 台灣時間 |
|---|---|---|
| `p0.yml` daily | `0 1 * * *` | 每天 09:00 |
| `full-regression.yml` weekly | `0 0 * * 1` | 每週一 08:00 |

注：GitHub cron 可能延遲幾分鐘到 1 小時，負載高時甚至 skip 該 schedule（無補跑機制）。

## Secrets 清單

`https://github.com/<owner>/<repo>/settings/secrets/actions` 設定，共 12 個：

| Site | Secrets |
|---|---|
| RC | `SITE_RC_URL` / `SITE_RC_USERNAME` / `SITE_RC_PASSWORD` |
| LT | `SITE_LT_URL` / `SITE_LT_USERNAME` / `SITE_LT_PASSWORD` |
| RE | `SITE_RE_URL` / `SITE_RE_USERNAME` / `SITE_RE_PASSWORD` |
| RD | `SITE_RD_URL` / `SITE_RD_USERNAME` / `SITE_RD_PASSWORD` |

### 用 `gh` CLI 從本機 .env 一次設好

```bash
for site in RC LT RE RD; do
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

不同 site 不同帳號 → matrix 4 job 可並行。

## 看 workflow run

進 `https://github.com/<owner>/<repo>/actions` → 點該 run。

run 頁面看得到：
- 各 job ✅/❌
- 每 step 完整 log
- **Job Summary**：pytest 測試結果以 markdown 表格顯示（pass/fail/skip 數量 + 失敗 test 名單），不用下載 artifact 即可 review
- **Artifacts**（頁面最下方）：
  - `report-html-<site>.zip` / `full-regression-report-<site>.zip`：自包式 HTML 報告
  - `failure-screenshots-<site>.zip`（**只有失敗時上傳**）：紅框截圖 + 自動生成 README.md

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

### 想升級成 hard block（PR merge 強制要求）

repo Settings → Branches → main → Add branch protection rule → Require status checks → 勾 `Docs Sync Check`。

當前未設 required check，PR 紅但仍可 merge（軟提醒）。
