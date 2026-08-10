# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

End-to-end regression test suite for a gaming platform using Python + pytest-playwright. Tests run against a live site via a Chrome browser, either locally or via CDP (Chrome DevTools Protocol) when running from WSL.

## Setup

依賴管理採 **uv 雙軌制**（D-022）：`pyproject.toml` + `uv.lock` 為 source of truth，`requirements.txt` 是 `uv export --no-hashes -o requirements.txt` 產出的鎖定版（**不可手改**，hook + CI 守門）。

```bash
cp .env.example .env   # Fill in credentials and CDP_URL
uv sync                # 推薦；或無 uv 時：python -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/playwright install chromium
```

改依賴 SOP：改 `pyproject.toml` → `uv lock` → `uv export --no-hashes -o requirements.txt` → 三檔一起 commit。

Key `.env` variables:
- `DEFAULT_SITE` — which site config to use (e.g. `rc`)
- `CDP_URL` — Chrome remote debug URL (WSL/Linux only; e.g. `http://<WINDOWS_IP>:9223`)
- `SITE_<NAME>_URL/USERNAME/PASSWORD` — per-site credentials

> **CDP 故障排除**：本機（WSL/CDP）跑測試若整批秒殺、錯誤為 `BrowserType.connect_over_cdp: Connection closed while reading from the driver`，**多半不是 Chrome 掛了**，而是 Chrome 上殘留 stuck service worker target（造訪過註冊 SW 的站就會留下）撞到 Playwright 的 assert。`conftest.py` 的 `_patch_playwright_crbrowser_sw_assert()` 會在每次啟動時自動 patch 本機 venv 的 driver 容忍它（**patch 不進 git，venv 重建 / Playwright 升版後會自動重套**）。若 Playwright 又改了 driver 版面導致 patch 失效，啟動時會印出提示，需更新該函式的 `_SW_PATCH_CANDIDATES` / `_SW_ASSERT_RE`。註：CI 走 `chromium.launch()` headless，不碰 CDP，不受影響。

## Running Tests

**Always use the project's virtualenv** located at `.venv/`:

```bash
.venv/bin/pytest                                                        # all tests
.venv/bin/pytest tests/rc/                                             # rc site only (no --site needed)
.venv/bin/pytest tests/lt/                                             # lt site only (no --site needed)
.venv/bin/pytest tests/lt/test_p0_smoke.py -m p0                         # lt p0 smoke tests
.venv/bin/pytest -m p0                                                  # by marker
.venv/bin/pytest -m login                                               # by marker
.venv/bin/pytest tests/rc/test_p0_smoke.py::TestLogin::test_login_success # single test
CI=true .venv/bin/pytest tests/rc/test_p0_smoke.py                      # 模擬 CI 模式：headless chromium 直接 launch（無 CDP）
```

Reports are written to `reports/report.html` (self-contained HTML).

## CI/CD

GitHub Actions 自動跑測試：

- `p0.yml`：PR 開啟（**draft 不跑**，轉 ready 才跑——draft 為施工中訊號，避免佔用共用測試帳號）/ push to main / 每天 09:00 台灣 / 手動 → RC + LT + RE + RD + QW + LG + LU + RF P0 smoke 8 站 matrix
- `full-regression.yml`：每週一 08:00 台灣 / 手動 → 8 站全套（P0 + feature）

> **KS（Super9娛樂城）已於 2026-07 永久退役**：站點下架，POM / 測試 / registry / marker / secrets 全數移除（本 repo 2026-08-05 清理）。歷史程式碼見 git 歷史（`git show 84bff6b:tests/ks/test_p0_smoke.py`）。
- `docs-sync-check.yml`（PR 靜態檢查集，三個 job）：`docs-sync-check` 驗 code 變動是否有對應 .md 更新（hook 機制 + CI 雙保險）；`factory-import-check` 驗 `tests/` 是否全走 factory（D-023，掃全樹）；`uv-requirements-sync` 驗 `requirements.txt` 與 `uv.lock` export 同步（`uv export --frozen` diff，不同步則紅）

**觀測性**：`p0.yml` 與 `full-regression.yml` 跑完後都有 `aggregate-summary` job — `.github/scripts/aggregate_test_results.py` 解析各站 JUnit XML 聚合成跨站成績單（含 **🔁 Flaky 欄／清單**＝重跑後才通過的 test，資料來自 `conftest.py` sessionfinish hook 產出的 `junit/<site>-flaky.json` sidecar；寫進 run 的 Step Summary），並可選推 Slack 通知（設了 `SLACK_WEBHOOK` secret 才推；排程一定推、PR/push 則失敗才推）。

詳細的 trigger 規則、cron 時段、secrets 清單、Slack/聚合成績單、如何看 run / 下載 artifact / 加 secret / debug fail → 見 [`docs/cicd.md`](docs/cicd.md)。

## Docs sync check（hook + CI 雙保險）

每次 commit / PR 自動檢查「code 變動是否同步更新 docs」：

- **Hook**（`.claude/settings.json` + `.github/scripts/check-docs-sync.sh`）：Claude 在跑 `git commit` 之前 block，stderr 提醒重看哪些 .md
- **CI**（`.github/workflows/docs-sync-check.yml`）：PR 時相同檢查跑一次，違規 → PR check 紅

確認**不**需要更新時的 override：
- commit message 加 sentinel `[skip-docs-check]` 並附理由
- 或設 env var `SKIP_DOCS_CHECK=1`

## Factory import guard（hook + CI 雙保險）

同款雙保險守 D-001 / D-002：`tests/` 內禁止直接 import 站點 POM（見 Multi-site Factory Pattern 段）。

- **Hook**（`.claude/settings.json` + `.github/scripts/check-factory-import.sh`）：`git commit` 前檢 staged 的 `tests/**/*.py`，違規 block
- **CI**（`docs-sync-check.yml` 的 `factory-import-check` job）：掃 `tests/` **全樹**（非 diff，可抓搬檔／改名逃逸），違規 → PR check 紅

判定採**例外法**：只放行 `from pages.factory import` 與 `from pages.dashboard.factory import`，其餘 `from pages.` 一律違規 —— 不硬編站點清單，新增站點零維護。

Override：commit message 加 `[skip-factory-check]` 並附理由，或設 env var `SKIP_FACTORY_CHECK=1`。

## 文檔維護對照表（code 變動 → 要同步的 doc）

**此表為文檔同步的唯一 source of truth**：`.github/scripts/check-docs-sync.sh` 的警示、`git-commit` skill Step 3、各 authoring skill / subagent 皆對齊此表。改 mapping 只動這裡。改 code 前先比對「我這次屬於哪一列、要連帶更新哪份 doc」，**root `README.md` 是第一公民，不要漏**。

| 變動類型 | 必須同步的 doc |
|---------|--------------|
| 新增 / 移除站點（`pages/<id>/`、`tests/<id>/`） | **README.md**（站台表 / 目錄樹 / 執行指令 / markers 表）+ **CLAUDE.md**（Architecture 樹 / 站點清單 / factory 段）+ `docs/README.md`（若新增 doc） |
| 新增 / 改名 pytest marker | **README.md** markers 表 + **CLAUDE.md** Markers + `pytest.ini` |
| 新增 / 改 fixture | **CLAUDE.md** Fixtures section |
| POM public method 改名 / 簽名變動 | 該 POM docstring +（若 CLAUDE.md 有提及該方法）**CLAUDE.md** |
| 新增 / 改 `utils/` helper | **CLAUDE.md** Architecture utils 區 + **README.md** utils 清單 |
| CI workflow / `.github/scripts` 變動 | **docs/cicd.md** + **CLAUDE.md** CI/CD 段 + **README.md** CI 表 |
| 新增 / 改名 / 刪 `.env` key | `.env.example` + **CLAUDE.md** Setup |
| VR / 截圖流程變動 | **CLAUDE.md** Visual Regression / Screenshot 段 |
| i18n 文案 / 站點 selector 慣例 | **docs/i18n_locale_text_reference.md** |
| 新增 `docs/` 檔 | **docs/README.md** 索引 + **README.md** 文件資源表 |
| 測試策略 / 覆蓋邊界 | **docs/testing-strategy.md** + **CLAUDE.md** Test Strategy |
| skill 流程變動 | 對應 `SKILL.md` + 其 frontmatter `description` |
| 團隊決策 / 協作協定變動 | **docs/decisions.md** + **CLAUDE.md** 雙人協作協定段 |

> 自動關卡（`check-docs-sync.sh`）對其中最高訊號的兩列加了 deterministic 硬規則：**新前台站點**、**marker 變動** 若沒同步 README + CLAUDE.md 會直接 block / PR 紅。其餘列靠本表 + skill/subagent 紀律 + reviewer 把關。

## Test Strategy

| 測試類型 | Fixture | Scope | 適用情境 |
|---------|---------|-------|---------|
| Smoke | `page` | function | 每次測試獨立 context，各自登入登出。驗證核心流程（登入/登出/首頁元素）。LT smoke 不使用 `logged_in_page`，避免 fixture 的 drawer 開關汙染截圖流程。 |
| Functional | `class_logged_in_page` + `go_home` | class | 一個 class 只登入一次，測試間共用 session，`go_home` 每個測試前回首頁。適合功能驗證。 |

各站點測試放在 `tests/<site_id>/` 下；smoke 測試統一命名 `test_p0_smoke.py`，功能型測試放 `tests/<site_id>/feature/<feature_name>/`。

**現金版前台存款覆蓋邊界**（LU/LG/QW）：一律不送出存款單（不可對稱回復，違反 D-015）、不為測試帳號綁銀行卡（單向操作且汙染共用帳號）。LU 無綁卡守衛可直接驗付款平台清單；LG/QW 未綁卡時存款頁會在約 1 秒後被導向銀行卡管理，故改驗「最終落點提供可操作下一步」。細節與 fail 判讀見 [`docs/testing-strategy.md`](docs/testing-strategy.md) 站點覆蓋邊界段。

## 測試結果判讀（Result Interpretation）

當測試失敗時，先區分「測試問題」還是「真實 FAIL」：

1. **檢視流程**：照截圖逐步確認 selector 命中、按鈕被按到、API 真的有送出 — 是否走完原本設計的 happy path？
2. **若流程無異常但結果非預期**（例如：點擊都成功但畫面顯示「連線失敗」、API 回傳錯誤碼、後續驗證找不到應有資料），**判定為真實 FAIL，不可加 `@pytest.mark.skip` 掩蓋**。
3. 真實 FAIL 通常代表**被測站點本身有 regression**（後端服務改動、產品 bug、資料配置壞掉）— 測試的職責就是揪出這個訊號。
4. 只有當問題明確屬於**測試自身**（selector 過時、timing race、test data 失效）才修測試碼或加 skip + 完整理由。

> 反例：dev-rc 遊戲 spin 後顯示「連線失敗 - 錯誤代碼 5305」，按鈕都點對了、API 也送了 — 這是 RD 改動造成遊戲後端壞掉的 regression FAIL，不該為了讓 CI 綠燈而 skip 該 test。

## Architecture

```
conftest.py                  — browser setup, environment detection (Windows/WSL/Linux), global fixtures
config/settings.py           — multi-site SiteConfig dataclass loaded from .env
pages/factory.py             — frontend: routes site_id → LoginPage/HomePage class via registry dict (no if/else fallback; unknown site_id raises ValueError)
pages/dashboard/factory.py   — backend dashboard: routes site_id → DashboardLoginPage/ManagementPage class (independent registry from frontend; no cross-import)
pages/rc/                   — rc site Page Objects (LoginPage, HomePage) — 王老吉娛樂城
pages/lt/                   — lt site Page Objects (LoginPage, HomePage) — LT來財
pages/re/                   — re site Page Objects (LoginPage, HomePage) — BeWin
pages/rd/                   — rd site Page Objects (LoginPage, HomePage) — 狗狗娛樂城
pages/qw/                   — qw site Page Objects (LoginPage, HomePage) — LM來財娛樂城（Nuxt/Vue，多語系 cookie 但無切換 UI＝實質單語系顯示）
pages/lg/                   — lg site Page Objects (LoginPage, HomePage) — 大撈家娛樂城（Nuxt/Vue，modal 登入）
pages/lu/                   — lu site Page Objects (LoginPage, HomePage) — Dlgbet（Nuxt/Vue，雙層彈窗 + 左側 sidebar 登出）
pages/rf/                   — rf site Page Objects (LoginPage, HomePage) — 金爺娛樂城（Nuxt/Vue 信用版，獨立 /Login 頁 + 登入三段 base-modal 確認彈窗）
pages/dashboard/<site_id>/   — backend dashboard page objects (DashboardLoginPage, ManagementPage); per dashboard factory registry
tests/api/<site_id>/         — API-layer tests (requests only, no browser, no pages/* import); per-site conftest
tests/dashboard/<site_id>/   — backend dashboard tests (rc/re/lt/rd 代理 top_up（代理→會員，皆信用版；lt/rd re-export RC POM，re subclass RC POM 僅覆寫 4 差異方法：Vue tab native click ×2 + `<a>` 名稱定位 ×2）；rd dialog 獨有操作者密碼欄位需傳 operator_password；**rc/re/lt/rd 另有總代→代理 top_up（站長層級 SITE_<ID>_DASHBOARD_USER，皆無 2FA；master_dashboard_page fixture）：代理 tab 每個下線代理為 .tab-item 卡（存入 btn-primary.me-2/提取 :not(.me-2)），總代額度 ∞ 故只驗代理側餘額（對稱可逆）；目標代理用 dashboard_agent_user；POM `set_agent_page_size(500)` 先把代理全載入 DOM（LT 166 代理分頁），`_agent_card` 用 tag-agnostic `.tab-item:has(:text-is(account))`，operator_password 傳 dashboard_pass（RD 有密碼欄、其他站自動略過）**；rf 信用版 站長+代理 login（皆無 2FA）+ 導航/logout + top_up（站長→會員）+ **總代→代理 top_up（站長即總代層級，複用 fresh_dashboard_page 不需新 fixture；RF 自有 POM 加 switch_to_agent_tab/deposit_to_agent 等，代理 tab 同會員 .tab-item 結構，dialog 餘額 label-xs[1]，總代 ∞ 只驗代理側）**；lu 站長帳號 login+TOTP 2FA + 導航/logout + **主錢包額度調整 top_up（站長專屬，會員管理→Main wallet 金額彈窗→增減，對稱可逆 + 額度歷史稽核驗證 #/report/balance-adjustment-report）**，及代理帳號 login（**2026-06-25 起代理也強制 2FA**，conftest 傳 dashboard_agent_totp）+ 導航/logout read-only smoke（代理點主錢包金額不開彈窗＝無充值權限）；lg/qw 代理 Vue admin smoke，re-export LU，空帳號故僅 smoke，其中 qw 代理需 2FA（conftest 傳 dashboard_agent_totp）；**lg/qw 皆有站長 login+TOTP 2FA + 主錢包 top_up（同 LU 模式，target=site_config.username）**。LU POM `_wallet_amount_locator` 用**內容定位**（含 Game wallet 按鈕的 td 內 div.bold）而非寫死欄位 index——各站 Main wallet 的 td index 不一致，內容定位跨站通用)；**信用版全家 rc/re/lt/rd/rf 另有 test_menu_entries.py 側欄入口檢測**（`menu_tree()` dump 頂層入口 route id + 各入口子入口 href，與 per-site spec 全等比對，站長+代理兩層級；spec 內嵌測試檔、文案僅註解；2026-07-30 probe 建立）；**現金版 lu/qw/lg 站長層級同款入口檢測 + lg 代理層級**（LU 型葉節點無 href → 子入口以顯示文字識別（sidebar_menu_tree_texts），頂層仍 route id；lu/qw 代理待 2FA TOTP 重綁定——2026-07-30 起 TwoFactorAuth/Verify 400，secret 疑遭伺服器端重綁）；**現金版 lu/lg/qw 另有 test_money_flow_pages.py 金流頁入口檢測 9 條**（存提審核頁 `#/member/member-deposit` / `member-deposit-store` / `member-withdraw` + 金流報表頁 `#/report/member-deposit` / `member-deposit-payment-report` / `member-withdrawal-report` / `memberPointRecord` / `wallet-history` / `balance-adjustment-report`；POM `goto_money_flow_page()` 用 route hash 直接 goto（葉節點無 href）+ `table_headers()` dump thead，與 spec 全等比對；三站 route 與欄位逐字全等，改版要三站一起改；2026-08-10 probe 建立）；**登出測試一律放 `test_zz_dashboard_logout.py`**——登出終結 session-scoped page fixture，pytest 依檔名字母序收集，`zz` 前綴確保它排最後（2026-08-10 前 lu/lg 因登出併在 navigation/agent 檔，全目錄跑時 test_menu_entries 固定失敗）; state-mutating tests should be reversible (rollback / teardown compensation)
tests/rc/                   — rc site tests (test_p0_smoke.py p0, feature/<name>/ p1: announcement_popup, i18n, navigation, wallet)
tests/rc/conftest.py        — rc-specific overrides: site_config=rc, go_home (+ dismiss announcement popup)
tests/lt/                   — lt site tests (test_p0_smoke.py p0, test_locale_visual_matrix.py p2 [skipped], feature/<name>/ p1: auth, copy, i18n, member, public, visual, wallet)
tests/lt/conftest.py        — lt-specific overrides: site_config=lt, page fixture without MutationObserver
tests/re/                   — re site tests (test_p0_smoke.py p0, feature/<name>/ p1: announcement_popup, copy, game, home_sections, i18n, member, navigation, sidebar, visual, wallet)
tests/re/conftest.py        — re-specific overrides: site_config=re, go_home
tests/rd/                   — rd site tests (test_p0_smoke.py p0, feature/<name>/ p1: announcement_popup, i18n, navigation)
tests/rd/conftest.py        — rd-specific overrides: site_config=rd, go_home
tests/qw/                   — qw site tests (test_p0_smoke.py p0, feature/<name>/ p1: navigation, announcement_popup, i18n, home_sections, member, sidebar, wallet, game (game launch skip：第三方 provider 後端未轉址，同 rc/re/rd); feature/copy p2 (含 title xfail：QW dev <title> 誤掛王老吉/RC 名); feature/visual/ p2)
tests/qw/conftest.py        — qw-specific overrides: site_config=qw, go_home (+ dismiss popup-mask)
tests/lg/                   — lg site tests (test_p0_smoke.py p0; feature/<name>/ p1: announcement_popup, navigation, member, wallet, i18n, game, sidebar, home_sections; copy p2; visual p2; modal 登入)
tests/lg/conftest.py        — lg-specific overrides: site_config=lg, go_home (+ dismiss 進站公告)
tests/lu/                   — lu site tests (test_p0_smoke.py p0; feature/<name>/ p1: announcement_popup, navigation, member, wallet, i18n, game, sidebar, home_sections; copy p2; visual p2; 雙層彈窗)
tests/lu/conftest.py        — lu-specific overrides: site_config=lu, go_home (+ dismiss 雙層彈窗)
tests/rf/                   — rf site tests (test_p0_smoke.py p0; feature/<name>/ p1: announcement_popup, navigation, member, wallet, i18n, game, sidebar, home_sections; copy p2; visual p2; 信用版 金爺娛樂城，Nuxt/Vue 三段彈窗登入)
tests/rf/conftest.py        — rf-specific overrides: site_config=rf, go_home (+ dismiss base-modal 彈窗)
utils/locale_helper.py       — set_locale(): injects i18n_locale cookie for lt site；switch_language_via_globe(): rc/re 型站點 globe icon UI 切語系（i18n 測試共用）
utils/dialog_helper.py       — helpers: dismiss server error popups, wait for loading animation；wait_login_loading(): 登入 loading 等待＋截圖（rc/rd/re LoginPage 共用）；clear_stuck_leave_overlay_if_present(): 清卡死的 Vue fade-leave 全屏遮罩（rd dev bug 家族）
utils/screenshot_helper.py   — element-highlight screenshot system, auto README.md generation; 圈選判定（scroll+bbox+視窗交集判 highlighted/reason/multi_match/oversize，寫 steps.json + README badge + PNG「未圈選」橫幅 + session _highlight_audit）+ written 缺圖自動回報（_write_screenshot 逾時 retry，未寫出標 ⚠️ 並列入 _highlight_audit）
utils/totp_helper.py         — get_totp_code(): pyotp TOTP 產碼 + 30s 窗口過期緩衝（後台 2FA，首用於 lu dashboard）
utils/game_launch_helper.py  — 遊戲啟動偵測共用 helper：new tab / provider 轉址判斷（lg/lu 型）+ open_in_new_tab() 點 launcher→等新分頁→maximize（lg/lu launch_game 共用，函式內零站點 selector）+ get_game_frame() 同分頁 canvas iframe 等待（rc/rd/re 型）+ site_base_domain() 站點可註冊網域推導（斷言不硬編 domain）
utils/menu_helper.py         — leaf_menu_texts()：選單容器葉節點短文字抽取（去重、保序；lg/lu user_menu_item_texts 共用，呼叫端傳入已開啟的選單 locator）
utils/layout_fingerprint.py  — 多語系版面健康度 DOM 指紋 + overflow 偵測（locale_layout / visual 用）
utils/visual_helpers.py      — VR 共用邏輯：save_vr_screenshot() / screenshot_with_mask()（詳見 Visual Regression 段）
utils/window_helper.py       — 另開分頁（遊戲 launch new tab）後 CDP 最大化視窗
utils/wait_helpers.py        — 可判定等待 helper：wait_for_text_matches()（等元素文字符合 pattern）/ wait_for_nonempty_text()（\S 特例）；讀值前取代散落硬等，用於 rf/rc/re/lt/rd dashboard 餘額讀取
utils/api_helpers.py         — API 測試共用邏輯（純函式）：api_base_url_for / api_headers_for / login_for_token；各站 tests/api/<id>/conftest.py 的 fixture 仍 per-site（session 快取跨站隔離），只 body 呼叫這些函式
utils/home_reset.py          — go_home 共用邏輯：reset_home_with_dismissers（rc/re/rd 型）/ reset_home_with_home_popups（qw/lg/lu/rf 型）；各站 conftest go_home fixture body 呼叫
utils/dashboard_helpers.py   — 後台 login fixture 共用 generator dashboard_login_session（建 context 複用 _new_configured_page + factory 登入 + 可選 screenshotter + totp sentinel）；各站 dashboard conftest login fixture 用 yield from（fixture 仍 per-site 避免 session 快取跨站污染）；sidebar_menu_tree()：側欄選單樹 dump（入口檢測用；等 href 非同步掛載後一次 evaluate，回傳 [(parent route id, [子入口 href]), ...]）；sidebar_menu_tree_texts()：LU 型文字版（現金版葉節點無 href/id/class，子入口以顯示文字識別、頂層仍用 route id）
.github/scripts/aggregate_test_results.py  — 跨站 JUnit 聚合成績單（含 🔁 flaky 欄，讀 <site>-flaky.json sidecar；p0/full-regression 的 aggregate-summary job 共用）
.github/scripts/audit_highlights.py        — 離線重掃截圖圈選稽核（讀 steps.json 重建 _highlight_audit.md/.json，--fail-threshold 供 CI 門檻；與 write_highlight_audit 共用 _render_audit）
.github/scripts/check-docs-sync.sh         — docs sync check（hook + CI 共用）
screenshots/<site_id>/<timestamp>/<smoke|feature>/<test_name>/  — per-test screenshot folders, auto-categorized (in .gitignore)
screenshots/lt/vr_reference/                    — VR reference screenshots (no comparison, manual review only)
docs/                        — team-shared documentation (tracked in git)
dev-notes/                   — personal developer notes (gitignored except README.md)
```

**Environment detection** in `conftest.py`: detects WSL vs Windows vs Linux, auto-starts Windows Chrome over CDP if needed, injects a MutationObserver to auto-close server error popups.

**Fixtures** (conftest.py):
- `site_config` (session-scoped) — loads credentials for the selected site
- `page` (function-scoped) — fresh browser context per test, window maximized
- `logged_in_page` (function-scoped) — pre-authenticated page (RC smoke 使用；LT smoke 已改用 `page` 自行登入)
- `class_logged_in_page` (class-scoped) — logs in once per class; share session across functional tests
- `go_home` (function-scoped) — navigates back to home + clears popups before each functional test; use with `class_logged_in_page`
- `auto_screenshot` (autouse) — attaches `ScreenshotHelper` to page（涵蓋 `page` / `class_logged_in_page` / `dashboard_page` / `master_dashboard_page` / `agent_dashboard_page`）; auto-categorizes tests into `smoke/` or `feature/` subfolder; generates `screenshots/<site_id>/<timestamp>/<category>/<test_name>/README.md` after each test
- `auto_logout_after_test` (autouse) — logs out after each smoke test (`page` fixture only)

**Markers** (pytest.ini): `p0`, `p1`, `p2`, `login`, `home`, `member`, `wallet`, `i18n`, `language`, `copy`, `visual`, `visual_regression`, `locale_layout`, `docker_only`, `api`, `dashboard`, `game`, `flaky`, `no_toast_observer`, `lt`, `rc`, `re`, `rd`, `qw`, `lg`, `lu`, `rf`

## Multi-site Factory Pattern

`pages/factory.py` 使用兩個 registry dict 路由 `site_id` → page class：
- `_LOGIN_PAGE_REGISTRY`：`site_id` → `(module_path, class_name)`
- `_HOME_PAGE_REGISTRY`：同上
- 外部只透過 `get_login_page_class(site_id)` / `get_home_page_class(site_id)` 存取
- **不使用 if/else fallback 到預設站台**；未註冊的 `site_id` 必須拋 `ValueError`，訊息包含可用站台列表
- 新增站點只需在兩個 registry 各加一行，不動 function 邏輯

測試檔**禁止**直接 `from pages.<site_id>.xxx import ...`，必須透過 factory 取得 class 以維持跨站復用彈性。**`tests/` 樹下的非 `test_` 開頭 helper 檔（如 `tests/lt/feature/i18n/_locale_helpers.py`）同受此規範**——判準是「在 `tests/` 下且被測試 import」，不是檔名。

Canonical 寫法（module-level 綁定，全 repo 一致）：

```python
from pages.factory import get_login_page_class, get_home_page_class

LoginPage = get_login_page_class("rc")
HomePage = get_home_page_class("rc")
```

賦值必須早於該檔任何 module-level 使用點（例如函式簽名的型別註記），否則 `NameError`。

守門：`.github/scripts/check-factory-import.sh`（PreToolUse hook + `docs-sync-check.yml` 的 CI job 雙保險，D-023）。判定採例外法——`tests/` 內只放行 `from pages.factory import` 與 `from pages.dashboard.factory import`，其餘 `from pages.` 一律違規。Override：commit message 加 `[skip-factory-check]` 或 env `SKIP_FACTORY_CHECK=1`。

## Agent Skills

本 repo 有以下 user-invocable skills（位於 `.claude/skills/`），用於不同類型的工作：

| Skill | 用途 |
|-------|------|
| `ui-test-author` | 新增/修改 testcase、page object、fixture；含新增站點 onboarding checklist |
| `pom-architect` | 規劃/調整 Page Objects、component objects、multi-site UI 結構與跨站共用策略 |
| `test-review` | Review 測試變更，逐項檢查 flaky、脆弱 selector、multi-site 擴展性風險 |
| `git-commit` | 提交前檢查、整理 diff、建議驗證步驟與 commit message |
| `env-sync` | 維持 `.env` 與 `.env.example` 結構同步；處理同事發放的新 .env 範本合併 |
| `selector-probe` | 用 agent-browser CLI 即時 probe 網頁 selector / ARIA 結構，補強 chrome-devtools MCP 在「寫測試前探勘」與「pytest 失敗 root cause 分析」場景 |

各 skill 的指引與本 CLAUDE.md 互補：CLAUDE.md 是 repo 層級的 source of truth，skills 包含更詳細的 checklist 與實戰 pitfalls。Authoring 用 `ui-test-author`、設計 POM 用 `pom-architect`、review 用 `test-review`、commit 前用 `git-commit`、動 .env 用 `env-sync`、probe selector 用 `selector-probe`。

**完整接力工作流**（為什麼這 6 個 skill、如何接力、真實任務範例、避讓機制）見 [`docs/agent-skills-workflow.md`](docs/agent-skills-workflow.md)。

## Subagents

本 repo 還有 3 個 main agent 可主動派工的 subagent（位於 `.claude/agents/`，獨立 context 不污染主對話）：

| Subagent | 用途 | Inject 的 skill | 工具範圍 |
|---------|------|---------------|---------|
| `test-author` | 新增/修改 testcase、POM、實作功能驗證 | `ui-test-author`、`pom-architect` | Read/Write/Edit/Bash/Grep/Glob |
| `test-reviewer` | Read-only review、找 flaky / cover-up / 跨站風險 | `test-review` | Read/Grep/Glob/Bash |
| `selector-explorer` | DOM 探查、ARIA 拿 selector | `selector-probe` | Read/Grep/Glob/Bash |

Skill 是**人類**用 `/skill-name` 觸發；subagent 是 **main agent** 主動 delegate。詳細差異、三 agent 接力 SOP、避讓機制見 [`docs/agent-skills-workflow.md`](docs/agent-skills-workflow.md) 的 `## Subagent 層` 段。

**新站 onboarding 完整 SOP**（含 mermaid 流程圖、subagent / skill 觸發條件、QW 實作經驗的坑、預估時間）見 [`docs/new-site-onboarding-workflow.md`](docs/new-site-onboarding-workflow.md)。

## Documentation vs Developer Notes

This repo has **two distinct documentation folders** with different purposes and git-tracking policy. When creating or editing markdown files, pick the right folder and follow the convention.

### `docs/` — Team-shared, tracked in git

存放「**需要跨開發者共享、且相對穩定**」的文件。任何新加入的團隊成員應該能透過閱讀本資料夾建立對測試套件與產品的理解。

**應放入的內容**：
- 產品/技術**事實參考**（例如多語系文案對照、API 契約、測試資料定義）
- 測試策略與規格（測試方向、覆蓋原則、case 設計規範）
- 架構決策（page object 設計、fixture 分層、站台擴充方式）
- 慣例定義（命名規則、selector 策略、截圖規範）
- Onboarding 指南

**特徵**：不常變動、需要共識、跨開發者有效、新進成員必讀。

### `dev-notes/` — Personal, gitignored (except README.md)

存放「**個人的、經常變動的、不需團隊共識**」的工作筆記。文件僅代表撰寫者當下的觀察或想法，不是產品/測試的事實來源。

**應放入的內容**：
- 個人 TODO / 待辦清單、改善提案
- 探索筆記、實機發現、selector 嘗試紀錄
- Debug 紀錄、問題排查過程
- 效能實驗、benchmark 結果
- 想法草稿、未成熟的架構構想
- 測試覆蓋比對（與舊版/其他專案對照）

**特徵**：經常變動、個人觀點、可能未成熟、可丟棄。

**Git 設定**：`.gitignore` 設為 `dev-notes/*` 與 `!dev-notes/README.md`，只有 README 被追蹤。

### 判斷原則（when in doubt）

寫新文件前先問自己：

1. **「半年後任何人看到這份文件都能理解並受用嗎？」** → 是 `docs/` / 否 `dev-notes/`
2. **「這是產品/測試的事實，還是我目前的想法？」** → 事實 `docs/` / 想法 `dev-notes/`
3. **「新進成員需要讀這份文件才能上手嗎？」** → 需要 `docs/` / 不需要 `dev-notes/`

若某份 `dev-notes/` 的筆記後來成熟並獲得團隊共識，請**升級**移到 `docs/` 並調整內容為正式文件。反之，若 `docs/` 中某份文件變成僅個人觀點的 WIP 清單，應移到 `dev-notes/`。

## Visual Regression (lt / rc / qw / re / rd / lg / lu / rf)

LT、RC、QW、RE、RD、LG、LU、RF 皆採用 **reference screenshot** 策略：存檔供人工確認，不做 pixel 比對（跨環境解析度不穩定）。

```bash
# VR reference 截圖（輸出至 screenshots/<site_id>/vr_reference/）
.venv/bin/pytest tests/lt/feature/visual/test_visual_regression.py -m visual_regression
.venv/bin/pytest tests/rc/feature/visual/test_visual_regression.py -m visual_regression
.venv/bin/pytest tests/qw/feature/visual/test_visual_regression.py -m visual_regression
.venv/bin/pytest tests/re/feature/visual/test_visual_regression.py -m visual_regression
.venv/bin/pytest tests/rd/feature/visual/test_visual_regression.py -m visual_regression
.venv/bin/pytest tests/lg/feature/visual/test_visual_regression.py -m visual_regression
.venv/bin/pytest tests/lu/feature/visual/test_visual_regression.py -m visual_regression
.venv/bin/pytest tests/rf/feature/visual/test_visual_regression.py -m visual_regression

# DOM 層視覺健康度（非截圖）
.venv/bin/pytest -m visual
```

**架構**：
- 共用邏輯（`save_vr_screenshot` / `screenshot_with_mask`）集中在 `utils/visual_helpers.py`
- 各站動態元素 selector 放在 `tests/<site_id>/feature/visual/helpers.py` 的 `BANNER_SELECTORS`
- `screenshots/<site_id>/vr_reference/` 為 gitignored（依 `screenshots/` 全站規則），僅本機存放供人工 review
- 新增站點要加 VR：複製 `tests/<site_id>/feature/visual/` 模板，調整 BANNER_SELECTORS 與 test 檔中傳入 `save_vr_screenshot` 的 `site_id` 參數即可

**swiper 相容性**：部分站點 `.swiper-wrapper` / `.swiper-slide` 也命中 `.swiper` selector 但沒掛 swiper instance；`screenshot_with_mask` 用 optional chaining（`autoplay?.stop?.()`、`slideTo?.(0, 0)`）保護，不可回退成直呼 method。

> `tests/lt/test_locale_visual_matrix.py`（WIN-LVIS）目前全部 `skip`。

## Screenshot System

Every test automatically gets a `ScreenshotHelper` via the `auto_screenshot` autouse fixture. In POM methods and test files, use `get_screenshotter(page)` to access it:

```python
from utils.screenshot_helper import get_screenshotter

sh = get_screenshotter(page)
if sh: sh.capture(locator, "label")       # highlight element with red box → screenshot
if sh: sh.full_page("label")              # full-page screenshot (no element highlight)
```

Label naming convention:
- `click_XXX` → 點擊
- `fill_XXX` → 填入
- `verify_XXX` → 驗證
- `loading_XXX` → Loading 狀態

After each test, `screenshots/<site_id>/<timestamp>/<smoke|feature>/<test_name>/README.md` is auto-generated in Traditional Chinese with step-by-step screenshots embedded. Category is auto-detected: tests under `feature/` → `feature`, others → `smoke`.

### 圈選判定（Highlight audit）

`sh.capture(locator, label)` 不再靜默降級：`_highlight_and_screenshot` 會先 `scroll_into_view_if_needed`（解 below-fold）、`locator.count()`（偵測多命中）、取 `bounding_box` 並與視窗矩形比對，判定該次是否**真的圈到目標元素**，結果記進每步 metadata（`highlighted / reason / match_count / multi_match / oversize / written`）。契約不變——任何截圖/判定失敗都不 fail 測試。

失敗分類 `reason`：`no_match`（命中 0）/ `no_box`（取不到座標，元素隱藏或 detached）/ `zero_area`（零面積）/ `offscreen`（元素在視窗外）/ `bbox_error`（座標逾時）。`multi_match`（命中 >1，只圈第一個）與 `oversize`（框過大 >85% 視窗，圈了等於沒圈）為獨立旗標。

`written` 旗標＝**截圖檔是否真的寫出**：三個寫檔點（`full_page` / `_highlight_and_screenshot` / no_match 橫幅）統一走 `_write_screenshot()`，逾時先以 `animations="disabled"` retry 一次（凍結 CSS 動畫緩解忙碌 SPA 首頁 transient），仍失敗記 `written=False`（不拋出）。未寫出者 README 標 `⚠️ 截圖未寫出` 且不嵌壞圖連結，並列入 `_step_flawed` 瑕疵統計與 `_highlight_audit`（tag「截圖未寫出」）自動回報，不再依賴外掛 filesystem 比對。舊 `steps.json` 無此欄，判定一律用 `.get("written") is False` 向後相容。

判定產出（皆為觀測性、gitignored）：
- **PNG 橫幅**：圈選失敗的圖，畫面正中央注入紅底白字「未圈選：<原因>」橫幅（純前端注入，無新依賴）。
- **README badge**：瑕疵步驟標題加 `⚠️ 未圈到`／`⚠️ 截圖未寫出` + 中文原因；檔頭列 `截圖瑕疵步驟：N/M`（涵蓋圈選瑕疵與 full_page 未寫出）。
- **`steps.json`**：每個 test 資料夾一份機器可讀 step metadata。
- **`_highlight_audit.md` / `.json`**：`screenshots/<site>/<ts>/` 下的 session 級稽核成績單（`conftest.py` `pytest_sessionfinish` 呼叫 `write_highlight_audit()`），列出所有圈選有瑕疵的 test+step，取代人工逐張翻圖。
- **離線重掃**：`.github/scripts/audit_highlights.py <dir>` 純讀既有 `steps.json` 重建報告（不必重跑），`--fail-threshold N` 供 CI 門檻；與線上共用 `_render_audit()`。

## Coding Conventions

### 元素互動
一般元素互動前先呼叫 `scroll_into_view_if_needed()` 再 click/fill/type。

```python
element.scroll_into_view_if_needed()
element.click()
```

### 已知互動例外（改用 `dispatch_event("click")`）

以下情境 `.click()`（含 `force=True`）會固定 timeout 或丟 "Element is outside of the viewport"，必須改用 `dispatch_event("click")` 直接觸發 DOM event：

| 情境 | Selector 範例 | 原因 |
|------|---------------|------|
| RC CSS-hidden sidebar | `.sidebar-item.*`（`width=0` 容器） | 永遠在 viewport 外 |
| LT member drawer 按鈕（如登出） | drawer 內按鈕 | 渲染位置在 viewport 外 |
| 常駐 overlay backdrop 攔截點擊 | 如 LT drawer closed 狀態 | Pointer events 被攔截 |

### 其他互動規則
- **DOM re-render 後不要對舊 locator 呼叫 `scroll_into_view_if_needed()`**（element 可能 detached）。改用 `page.evaluate("window.scrollBy(0, N)")`。
- **Sidebar hidden nodes 與 content 同文案**（RC 站 `p.text-black`）：用 `p:not(.text-black)` 排除，避免 `text=XXX` 命中 hidden node。
- 禁止裸 `time.sleep()`，優先使用 Playwright `expect` 與可判定事件等待。

### Selector 規則
- **避免綁死文案**：placeholder / button name / footer tab 文字會隨 locale 變化（LT 多語系站），且即使單語系站台（RE/QW）也有 i18n hydration race 風險（placeholder 短暫為空）。使用 CSS-based selector（如 LT `input.input-style:not(.password-input)`、QW `input.auth-input__field[type='password']`、RE `input.input-style[type='text']`、`button.base-btn.type1`）或結構化 locator（如 `.footer-bg .content` 取 `.last`/`.nth(0)`）。
- **`.first` / `.last` 是 property，不是 method**：寫成 `.first()` 會觸發 `__call__` 錯誤。
- Selector 優先順序：穩定屬性 > role/結構化 locator > 穩定文案 > nth-child/深 CSS 鏈。

### LT SPA Login：必須等 `networkidle`
LT 使用 React SPA。若 form 在 `networkidle` 前被填入，登入 API 會成功但 SPA 不會離開 `/login`。前往 `/login` 時必須使用 `wait_until="networkidle"`。

### Exception Handling
只在預期元素缺席或 timeout 時 catch `PlaywrightTimeoutError`（`from playwright.sync_api import TimeoutError as PlaywrightTimeoutError`）。禁止 `except Exception: pass` 靜默 playwright 操作錯誤。

## Git Commit Rules

- 任何 commit / push 動作需先經使用者確認。
- **禁止**在 commit message 加入 `Co-Authored-By: Claude ...` 或任何 Claude 署名。
- **Commit message 風格（D-021，hook 強制）**：subject 一律**簡潔英文** `type(scope): summary`（≤72 字元，禁 CJK；types: feat/fix/test/chore/docs/refactor/ci/perf/revert/wip）。細節、理由、`[skip-docs-check] <短理由>` 放 **body（第二個 `-m`）**，body 不限語言。PR title 遵守同規則（squash-merge 後即 main 的 commit subject）；詳細脈絡寫在 PR description，不塞 commit。守門：`.github/scripts/check-commit-msg.sh`（PreToolUse hook，違規 block；`SKIP_COMMIT_MSG_CHECK=1` 可 override）。

## 雙人協作協定(並行開發)

兩位開發者(nohungry 主、Luke 次)並行開發,各自使用自己的 Claude Code;個人 Claude memory 為 machine-local **不進 git**。協調訊號放在雙方已共享的通道(repo + GitHub),架構決策見 [`docs/decisions.md`](docs/decisions.md)(決策條目的新增/修訂規則見該檔檔頭)。

### 開工協定(動工任何 feature / 重構前)

1. **讀 `docs/decisions.md` 相關條目** — 與既有決策衝突的寫法不可逕行動工;做法有多種且無對應決策 → 先以 PR 新增 `proposed` 條目,由 nohungry 拍板改 `accepted` 再動工(**架構決策的最終解釋權在 nohungry;Luke 提交的 PR 由 nohungry review**)。
2. **查對方 in-flight 工作**:`gh pr list --state open` 檢視對方 open/draft PR 的範圍。
3. **碰撞偵測**:比對「本次計畫要動的檔案」與對方 PR 的 `gh pr diff <n> --name-only` 是否有交集;有 codebase-memory MCP 的機器可再沿呼叫關係反查間接相依(無此 MCP 則略過該層,屬 best-effort 加值)。有交集 → 先與對方協調,不硬擋。
4. **開 draft PR 宣告施工**:第一個真 commit 後即開 draft PR(不必等功能完成),描述寫明:範圍(站點 / 檔案 / feature)+ **使用中的站點測試帳號**(配合同帳號不並行規則,對方動測試前先看)。功能完成後轉 ready for review。

### commit 前

git-commit skill 內含碰撞檢查 step(對方的新 PR 可能在開工後才出現),見該 skill。

### Memory 政策

個人 memory 維持私有;「對團隊有效」的知識(架構決策、站點陷阱、慣例)應蒸餾進 `docs/`(決策類進 `docs/decisions.md`),**蒸餾時嚴禁帶出憑證(帳號 / 密碼 / TOTP / .env 值)與個人筆記**。
