# Auto Regression - Platform 自動化回歸測試

使用 **Python + pytest-playwright**，針對多個遊戲站台進行端對端回歸測試，支援 Windows / WSL / Linux / CI 四種環境自動偵測。

## 支援站台

站台一律以代號敘述；實際網址與帳號見 `.env` 的 `SITE_<ID>_*` keys。

| 站台 ID | 網址 | 測試數 |
|---------|------|--------|
| `rc` | 見 .env `SITE_RC_URL` | 63 |
| `lt` | 見 .env `SITE_LT_URL` | 112 |
| `re` | 見 .env `SITE_RE_URL` | 63 |
| `rd` | 見 .env `SITE_RD_URL` | 58 |
| `qw` | 見 .env `SITE_QW_URL` | 48 |
| `lg` | 見 .env `SITE_LG_URL` | 44 |
| `lu` | 見 .env `SITE_LU_URL` | 43 |
| `ks` | 見 .env `SITE_KS_URL` | 43 |
| `rf` | 見 .env `SITE_RF_URL` | 48 |
| API | (9 站，不啟動瀏覽器) | 102 |
| Dashboard | (9 站後台) | 51 |

> 測試數以 `.venv/bin/pytest tests/<site>/ --collect-only -q` 為準，會隨新增測試變動。

## 目錄結構

```
conftest.py                          — 全域 fixtures、環境偵測（Windows/WSL/Linux/CI）、MutationObserver 注入
config/settings.py                   — 多站台 SiteConfig，從 .env 讀取
pages/factory.py                     — 前台：site_id → LoginPage/HomePage 路由（registry dict）
pages/dashboard/factory.py           — 後台：site_id → DashboardLoginPage/ManagementPage 路由
pages/<site_id>/                     — 各站前台 Page Objects（rc/lt/re/rd/qw/lg/lu/ks/rf 共 9 站）
pages/dashboard/<site_id>/           — 各站後台 Page Objects（9 站）
tests/<site_id>/                     — 各站前台測試（rc/lt/re/rd/qw/lg/lu/ks/rf；含 test_p0_smoke.py + feature/）
tests/api/<site_id>/                 — API 層測試（9 站，不啟動瀏覽器，requests 直打 API）
tests/dashboard/<site_id>/           — 後台管理介面測試（9 站）
utils/locale_helper.py               — set_locale()：注入 `i18n_locale` cookie（LT 用）；switch_language_via_globe()：globe icon UI 切語系（RC/RE i18n 測試共用）
utils/dialog_helper.py               — 伺服器錯誤彈窗、公告彈窗（含 MutationObserver enforce killer）、Loading 等待；wait_login_loading()：登入 loading 等待＋截圖（RC/RD/RE LoginPage 共用）；clear_stuck_leave_overlay_if_present()：清卡死的 Vue fade-leave 遮罩（KS/RD dev bug 家族）
utils/screenshot_helper.py           — 截圖系統（元素高亮 + 自動產生繁中 README；圈選判定：scroll+bbox 判是否真圈到，寫 steps.json / README badge / PNG「未圈選」橫幅 / session _highlight_audit）+ written 缺圖自動回報（寫檔逾時 retry，未寫出標 ⚠️ 並列入稽核）
utils/visual_helpers.py              — VR reference 截圖 + 動態元素遮蔽
utils/totp_helper.py                 — get_totp_code()：後台 2FA TOTP 產碼（pyotp + 30s 窗口緩衝）
utils/game_launch_helper.py          — 遊戲啟動偵測：new tab / provider 轉址判斷（LG/LU/KS 型）+ get_game_frame() 同分頁 canvas iframe 等待（RC/RD/RE 型）+ site_base_domain() 站點可註冊網域推導（斷言不硬編 domain）
utils/layout_fingerprint.py          — 多語系版面健康度 DOM 指紋 + overflow 偵測
utils/window_helper.py               — 另開分頁後 CDP 最大化視窗
utils/wait_helpers.py                — 可判定等待（wait_for_text_matches / wait_for_nonempty_text：讀值前等文字符合/非空，取代硬等）
utils/api_helpers.py                 — API 測試共用邏輯（env 推導 / headers / 登入拿 token；各站 conftest fixture 保持 per-site）
utils/home_reset.py                  — go_home 共用邏輯（回首頁 + 清彈窗兩型：dialog-dismisser / HomePage.dismiss_any_popups）
utils/dashboard_helpers.py           — 後台 login fixture 共用 generator（建 context + factory 登入 + 可選 screenshotter/2FA；各站 fixture 保持 per-site）
.github/workflows/                   — GitHub Actions（p0 / full-regression / docs-sync-check）
.github/scripts/                     — CI 共用 script（check-docs-sync.sh + aggregate_test_results.py 跨站聚合成績單 + audit_highlights.py 離線截圖圈選稽核）
.claude/                             — Claude Code 配置（hooks / skills / agents，團隊共用）
docs/                                — 團隊共用文件（追蹤於 git）
dev-notes/                           — 個人開發筆記（gitignored，僅 README 追蹤）
screenshots/                         — 截圖與報告，自動分為 smoke/ 與 feature/（gitignored）
reports/report.html                  — pytest-html 測試報表（gitignored）
```

> 詳細的角色分工與架構決策見 [`CLAUDE.md`](CLAUDE.md)；docs 子資料夾索引見 [`docs/README.md`](docs/README.md)。

## 安裝

```bash
cp .env.example .env        # 填入站台帳號密碼與 CDP_URL
pip install -r requirements.txt
playwright install chromium
```

## 執行

**請使用專案 virtualenv（`.venv/`）執行所有指令。**

```bash
.venv/bin/pytest                                                          # 全部測試
.venv/bin/pytest tests/rc/                                               # rc 站
.venv/bin/pytest tests/lt/                                               # lt 站
.venv/bin/pytest tests/re/                                               # re 站
.venv/bin/pytest tests/rd/                                               # rd 站
.venv/bin/pytest tests/qw/                                               # qw 站
.venv/bin/pytest tests/lg/                                               # lg 站
.venv/bin/pytest tests/lu/                                               # lu 站
.venv/bin/pytest tests/ks/                                               # ks 站
.venv/bin/pytest tests/rf/                                               # rf 站
.venv/bin/pytest tests/api/                                              # 僅 API 測試
.venv/bin/pytest tests/dashboard/                                        # 僅後台測試
.venv/bin/pytest tests/lt/test_p0_smoke.py -m p0                         # lt P0 smoke
.venv/bin/pytest -m p0                                                    # 所有站台 P0
.venv/bin/pytest -m "lt and i18n"                                        # lt 多語系測試
.venv/bin/pytest tests/rc/test_p0_smoke.py::TestLogin::test_login_success # 單一測試
CI=true .venv/bin/pytest tests/rc/test_p0_smoke.py                       # 模擬 CI 模式：headless chromium 直接 launch（無 CDP）
```

### 查看 HTML 報表

```bash
explorer.exe reports/report.html   # WSL
```

## CI/CD

GitHub Actions 自動跑測試與 docs 同步檢查：

| Workflow | 觸發 | 跑什麼 |
|---|---|---|
| `.github/workflows/p0.yml` | PR（draft 不跑）/ push to main / daily 09:00 台灣 / 手動 | 9 站 P0 smoke matrix（rc/lt/re/rd/qw/lg/lu/ks/rf） |
| `.github/workflows/full-regression.yml` | 週一 08:00 台灣 / 手動 | 9 站全套（P0 + feature；不由 PR/push 觸發） |
| `.github/workflows/docs-sync-check.yml` | PR | code 變動是否同步更新 docs |

p0 / full-regression 跑完都會由 `aggregate-summary` job（`.github/scripts/aggregate_test_results.py`）把各站結果聚合成跨站成績單寫進 run Step Summary（含 **🔁 Flaky 欄**＝重跑後才通過的 test，來自 `conftest.py` 產出的 `junit/<site>-flaky.json` sidecar），並可選推 Slack（設 `SLACK_WEBHOOK` secret 才推；排程必推、PR/push 失敗才推）。

操作細節（trigger 規則、cron 時段、secrets 清單、Slack 通知 + 聚合成績單、看 run / 下載 artifact / debug、docs sync check 操作 + override）見 [`docs/cicd.md`](docs/cicd.md)。

## WSL 設定

### 1. Windows Chrome 啟用 remote debugging

PowerShell（系統管理員）一次設好 portproxy（永久生效）：

```powershell
netsh interface portproxy add v4tov4 listenport=9223 listenaddress=0.0.0.0 connectport=9223 connectaddress=127.0.0.1
```

### 2. 設定 .env

```
CDP_URL=http://<WINDOWS_IP>:9223
```

查詢 Windows IP：
```bash
ip route show | grep -i default | awk '{print $3}'   # WSL 預設 gateway = Windows host
```

### 3. 執行測試

`conftest.py` 偵測到 WSL 後，若 Chrome 尚未啟動會自動呼叫 `chrome.exe --remote-debugging-port=9223`，不需手動開啟瀏覽器。

完整 port forwarding / 防火牆說明見 [PORTS_AND_SETUP.md](PORTS_AND_SETUP.md)。

## 環境對照

| 環境 | 瀏覽器啟動方式 | conftest 分支 |
|------|----------------|----------------|
| Windows | Playwright 直接啟動 Chrome | `sys.platform == 'win32'` |
| WSL | 自動啟動 Windows Chrome，CDP 連接（port 9223） | `_is_wsl()` |
| 純 Linux（非 CI） | 手動啟動 Chrome `--remote-debugging-port=9222`，設 `CDP_URL` | else |
| **CI（GitHub Actions）** | **Playwright 內建 chromium headless（無需 CDP）** | **`_is_ci()` → 由 `CI=true` env var 觸發** |

## 測試分級與 Markers

### 優先級

| Marker | 說明 |
|--------|------|
| `p0` | 核心 Smoke，每次 Release 必跑 |
| `p1` | 功能驗證，重大版本必跑 |
| `p2` | 視覺/完整回歸 |

### 站台

站台 marker 與站台 ID 同名：`rc` / `lt` / `re` / `rd` / `qw` / `lg` / `lu` / `ks` / `rf`。

### 功能 / 其他

| Marker | 說明 |
|--------|------|
| `login` / `home` / `member` / `wallet` | 功能領域 |
| `i18n` / `language` / `copy` | 多語系 / 文案 |
| `visual` / `visual_regression` / `locale_layout` | 視覺 |
| `api` / `dashboard` / `game` | 測試類別 |
| `flaky` | 已知偶發 flaky，附理由 |
| `no_toast_observer` | 停用全域 toast auto-close observer（需斷言 toast 可見的 test） |
| `docker_only` | 僅 Docker 環境（pixel-level snapshot） |

> 完整 markers 定義與測試分層、flaky 處理原則見 [`pytest.ini`](pytest.ini) 與 [`docs/testing-strategy.md`](docs/testing-strategy.md)。

## 文件資源

| 路徑 | 用途 |
|------|------|
| [`CLAUDE.md`](CLAUDE.md) | Claude Code / agent 協作指南、慣例定義、架構說明 |
| [`docs/`](docs/) | 團隊共用的事實/策略/規格文件 |
| [`docs/cicd.md`](docs/cicd.md) | GitHub Actions 操作指南 |
| [`docs/testing-strategy.md`](docs/testing-strategy.md) | 測試分層、通過標準、flaky 處理 |
| [`docs/i18n_locale_text_reference.md`](docs/i18n_locale_text_reference.md) | 多語系文案對照表（LT 5 + RC 6 + RD 5） |
| [`docs/agent-skills-workflow.md`](docs/agent-skills-workflow.md) | Agent / skill / subagent 接力工作流 |
| [`docs/new-site-onboarding-workflow.md`](docs/new-site-onboarding-workflow.md) | 新站 onboarding 完整 SOP（流程圖、subagent/skill 觸發、踩坑） |
| [`docs/lt-dashboard-sitemap.md`](docs/lt-dashboard-sitemap.md) | LT 後台 25 頁功能地圖 |
| [`docs/dashboard-technical-notes.md`](docs/dashboard-technical-notes.md) | 後台測試技術注意事項 |
| [`docs/product-bugs-to-report.md`](docs/product-bugs-to-report.md) | 已確認待回報的產品/前端/後端 bug 清單 |
| [`docs/decisions.md`](docs/decisions.md) | 團隊架構決策紀錄（並行開發的架構共識層） |
| [`PORTS_AND_SETUP.md`](PORTS_AND_SETUP.md) | Port 轉發與環境設定 |
| [`dev-notes/`](dev-notes/) | 個人開發筆記（gitignored） |

## 說明

- **多站台支援**：在 `.env` 增加 `SITE_<X>_URL / USERNAME / PASSWORD`，於 `pages/<site_id>/` 建立 Page Objects，在 `pages/factory.py` 的 registry dict 註冊，再於 `tests/<site_id>/` 建立測試目錄即可（dashboard 走 `pages/dashboard/factory.py` 同模式）
- **伺服器錯誤彈窗**：`conftest.py` 內建 MutationObserver 注入，自動處理 rc 站的伺服器錯誤彈窗；lt 站在 `tests/lt/conftest.py` 覆寫 `page` fixture 關閉此注入（避免 lt 錯誤 dialog 撞同 selector）
- **截圖系統**：每個測試自動截圖並高亮操作元素（紅框），存於 `screenshots/<site_id>/<timestamp>/<smoke|feature>/<test_name>/`，自動依測試路徑分類，並產生繁中操作流程 README
- **報表與截圖**：`reports/`、`screenshots/` 均已加入 `.gitignore`
- **Docs sync check**：commit 時自動檢查 code 變動有沒有對應 .md 更新（hook + CI 雙保險），見 [`docs/cicd.md`](docs/cicd.md)
