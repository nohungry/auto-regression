# 團隊架構決策紀錄(Decisions)

雙人並行開發的**架構共識層**:每條決策記「決定了什麼 / 為什麼 / 不採的替代方案 / 影響範圍」,防止「同一需求兩種架構寫法」進到同一個 repo。

**使用規則**(流程細節見 CLAUDE.md「雙人協作協定」):

- 設計新功能 / 重構前**必讀相關條目**;與條目衝突的寫法不可逕行動工。
- 要做的事「做法有多種、且此處無對應決策」→ 先以 PR 新增一條 `proposed` 條目,**由 nohungry 拍板**改 `accepted` 後才動工(架構決策的最終解釋權在 nohungry;異議在 PR 上提出討論)。
- 修訂既有決策:不改寫歷史條目,新增一條新決策並在舊條目標 `superseded by D-xxx`。
- 條目來源:初始 D-001~D-018 為 2026-07 從既有實踐(CLAUDE.md、review 紀錄、開發教訓)**追認**;新條目由日常開發產生。

---

## D-001 Multi-site 路由用 registry dict,無 fallback

- 狀態:accepted(追認)
- 決策:`pages/factory.py` / `pages/dashboard/factory.py` 用 registry dict 路由 `site_id` → POM class;未註冊的 site_id 一律拋 `ValueError`(訊息含可用站台),**不 fallback 到預設站**。測試檔禁止直接 `from pages.<site_id> import`,必須走 factory。
- 理由:fallback 會讓錯誤配置(打錯站名、漏註冊)靜默用錯站跑完;direct import 會讓跨站復用與站點替換失去彈性。
- 影響:`pages/factory.py`、`pages/dashboard/factory.py`、所有測試檔。

## D-002 前台與後台 factory 各自獨立

- 狀態:accepted(追認)
- 決策:前台 `pages/factory.py` 與後台 `pages/dashboard/factory.py` 是兩個獨立 registry,互不 cross-import。
- 理由:前後台站點集合、POM 介面、演進速度都不同;綁在一起會互相牽制。
- 影響:新增站點時兩處(若前後台皆有)各自註冊。

## D-003 Smoke 與 Functional 用不同 fixture 分層

- 狀態:accepted(追認)
- 決策:Smoke 用 function-scoped `page`(每測獨立 context、各自登入登出);Functional 用 class-scoped `class_logged_in_page` + `go_home`(一個 class 登入一次)。
- 理由:smoke 驗核心流程需完全隔離;functional 重複登入成本高且會觸發站方 session 限制。
- 影響:`conftest.py` fixtures、所有 `tests/<site_id>/`。例外:LT smoke 不用 `logged_in_page`(fixture 的 drawer 開關會汙染截圖流程)。

## D-004 Session/class fixture 不抽共用父 conftest

- 狀態:accepted(追認,2026-07 Phase 3 實測)
- 決策:跨站共用邏輯抽成 `utils/` **純函式** + 各站 conftest 保留 per-site fixture(body 呼叫共用函式或 `yield from` generator);**不**把 session/class-scoped fixture 上移到共用父 conftest。
- 理由:session fixture 放共用層會讓快取跨站污染(A 站 token 被 B 站拿到)— Phase 3 API dedup 實測踩坑後定案。
- 替代方案:共用父 conftest(不採,如上);完全不 dedup(不採,Phase 3 累計 -1560 行證明 dedup 值得)。
- 影響:`utils/api_helpers.py`、`utils/home_reset.py`、`utils/dashboard_helpers.py` 與各站 conftest。

## D-005 VR 用 reference screenshot,不做 pixel 比對

- 狀態:accepted(追認)
- 決策:9 站 visual regression 一律「存 reference 截圖供人工 review」,不做自動 pixel diff。
- 理由:跨環境(本機/CI/不同解析度)pixel 不穩定,自動比對偽陽性淹沒真訊號。
- 影響:`utils/visual_helpers.py`、`tests/<site_id>/feature/visual/`。

## D-006 禁裸 time.sleep,等待必須可判定

- 狀態:accepted(追認)
- 決策:等待一律用 Playwright `expect` 或 `utils/wait_helpers.py` 的可判定等待(`wait_for_text_matches` 等);禁止裸 `time.sleep()`。
- 理由:硬等在慢環境 flaky、在快環境浪費;可判定等待兩者兼顧且失敗訊息可診斷。
- 影響:全 repo;dashboard 餘額讀取已遷移(僅 LU 因真守衛硬等 + 2FA 風險刻意保留,見該站 conftest 註記)。

## D-007 Viewport 外元素的互動例外走 dispatch_event

- 狀態:accepted(追認)
- 決策:預設互動是 `scroll_into_view_if_needed()` + `click()`;僅 CLAUDE.md「已知互動例外」表列的情境(CSS-hidden sidebar、drawer 外按鈕、overlay backdrop 攔截)改 `dispatch_event("click")`。
- 理由:這些情境 `.click()` 含 `force=True` 都會固定 timeout;但 dispatch_event 繞過真實使用者行為,不可濫用成預設。
- 影響:各站 POM;新增例外情境需回填 CLAUDE.md 該表。

## D-008 Selector 不綁死文案

- 狀態:accepted(追認)
- 決策:selector 優先順序:穩定屬性 > role/結構化 locator > 穩定文案 > nth-child/深 CSS 鏈;placeholder / 按鈕文字這類 locale 相關文案不可當定位依據。
- 理由:多語系站文案隨 locale 變;單語系站也有 i18n hydration race(文案短暫為空)。
- 影響:所有 POM 與測試檔。

## D-009 真實 FAIL 不以 skip 掩蓋

- 狀態:accepted(追認)
- 決策:流程無異常但結果非預期(API 錯誤碼、畫面顯示連線失敗)→ 判定**真實 FAIL**,不加 skip 讓 CI 綠燈;測試從 pass 轉 fail 先通知另一位開發者確認原因,再決定修測試或報產品 bug。只有問題明確屬於測試自身(selector 過時、timing race、test data 失效)才修測試 / skip + 完整理由。
- 理由:測試的職責就是揪出站點 regression;skip 掩蓋等於廢掉測試。
- 影響:所有測試;產品 bug 記入 `docs/product-bugs-to-report.md`。

## D-010 每個可判定步驟必截圖;截圖失敗不 fail 測試

- 狀態:accepted(追認)
- 決策:新增 / 修改測試時每個可判定步驟都要 `sh.capture()` / `full_page()` 截圖(無截圖視為不合格);同時截圖系統的任何失敗(圈選失準、寫檔逾時)只記 metadata 回報,**不**讓測試本身 fail。
- 理由:截圖是人工判讀與稽核的證據鏈;但觀測性工具自身故障不該汙染測試結果。
- 影響:`utils/screenshot_helper.py`(圈選判定、written 旗標、audit 管線)、所有測試。

## D-011 同帳號不並行

- 狀態:accepted(追認)
- 決策:同一個測試帳號不可同時跑兩個 pytest process(本地 × 本地、本地 × CI 皆然);CI 以每帳號 concurrency group 防撞。
- 理由:站方後端互踢 session,造成大量非真實失敗。
- 影響:本地執行紀律、`.github/workflows/` concurrency 設定。**並行開發時尤其注意:兩人同時對同一站跑測試會互踢,動測試前先看對方 draft PR 標注的使用站點。**

## D-012 main 只收 PR

- 狀態:accepted(追認)
- 決策:不在 main 直接開發 / commit / push;一律 feature branch + PR + CI 綠 + squash-merge。stacked PR 時底層 squash-merge 不可帶 `--delete-branch`(會 close 上層且無法 reopen);協作類 PR 預設互相獨立、不 stacked。
- 理由:PR 是兩人協作的 review 與感知節點;stacked 教訓為實際事故。
- 影響:所有開發流程。

## D-013 docs/ 與 dev-notes/ 分流

- 狀態:accepted(追認)
- 決策:團隊共識、跨開發者有效、相對穩定 → `docs/`(git tracked);個人、常變動、未成熟 → `dev-notes/`(gitignored)。dev-notes 筆記成熟後升級進 docs。code 變動與 doc 同步由 docs-sync check(hook + CI)把關,對照表以 CLAUDE.md 為唯一 source of truth。
- 理由:讓「事實」與「想法」有明確界線,新成員讀 docs/ 就能上手。
- 影響:所有 .md 的落點決策。

## D-014 Credentials 只存 .env

- 狀態:accepted(追認)
- 決策:帳號 / 密碼 / TOTP secret / 帶認證 URL 一律 `.env` + `config/settings.py` 讀取;docs、skill、註解、commit 一律用佔位範例(`xxxx001` 類)。`.env` 動則 `.env.example` 同步(只有 key 無值)。
- 理由:repo 會被多人與多個 AI session 讀取,任何硬寫憑證都是洩漏面。
- 影響:全 repo;git-commit skill Step 0 有 deterministic 掃描。

## D-015 後台 state-mutating 測試必須可逆

- 狀態:accepted(追認)
- 決策:後台會改資料的測試(top_up 等)設計成對稱可逆(存入 ↔ 提取)或帶 teardown 補償;無法可逆的操作不納入自動化。
- 理由:測試環境資料是兩人共用的,單向汙染會讓對方的測試與人工驗證失準。
- 影響:`tests/dashboard/`。

## D-016 測試以平台為主,第三方遊戲次要

- 狀態:accepted(追認)
- 決策:覆蓋重點是網站 / 平台功能;單款遊戲內部品質不深測(多為 provider 問題),遊戲類測試驗到「成功啟動 / 轉址」為止。
- 理由:遊戲 provider 非我方可控,深測產出的 fail 無人能修。
- 影響:`tests/<site_id>/feature/game/`、`utils/game_launch_helper.py`。

## D-017 後台 2FA:站長預設有、代理條件式

- 狀態:accepted(追認)
- 決策:站長層級後台帳號預設要求 2FA TOTP(`utils/totp_helper.py`);代理層級用條件式偵測(有 TOTP 欄位才填,無則跳過)。
- 理由:各站 / 各層級 2FA 政策不一且會變(LU 代理 2026-06-25 起強制),條件式避免政策切換時全面翻修。
- 影響:`tests/dashboard/` conftest、`utils/dashboard_helpers.py`。

## D-018 截圖 / 圈選瑕疵走 audit 管線,不靠人工翻圖

- 狀態:accepted(追認)
- 決策:圈選判定(highlighted / reason)與寫檔判定(written)記入 steps.json,session 級 `_highlight_audit` 自動聚合回報;離線可用 `.github/scripts/audit_highlights.py` 重掃。
- 理由:9 站每輪數百張截圖,人工逐張翻不可持續;判定先行、憑證據修呼叫點。
- 影響:`utils/screenshot_helper.py`、`conftest.py` sessionfinish、CI。

---

## D-019 雙人並行開發協作協定

- 狀態:accepted(2026-07 隨協定 PR 生效)
- 決策:並行開發用兩個共享載體協調 —— ① 本檔(`docs/decisions.md`)為架構共識層;② **draft PR 為「施工中」訊號**:第一個真 commit 後即開 draft PR,描述寫明範圍(站點 / 檔案 / feature)與**使用中的站點帳號**(配合 D-011)。開工前與 commit 前做碰撞偵測(對方 open PR 的檔案交集;有 codebase-memory 的機器加呼叫鏈相依反查,無則略過該層)。個人 Claude memory 維持私有不進 git,團隊有效知識蒸餾進 docs。流程細節見 CLAUDE.md「雙人協作協定」段。
- 理由:兩人各用各的 Claude Code、memory 互不可見,撞工與架構分歧需要 git/GitHub 這個雙方已有的共享通道承載協調訊號;memory 含憑證線索與個人筆記,不可直接 git track。
- 替代方案:共用 memory 目錄進 git(不採:機密與個人觀點無法分離);共享記憶伺服器(不採:2 人規模 overkill、憑證管理風險);每 feature 強制 plan 檔(不採:draft PR 描述已覆蓋)。
- 影響:CLAUDE.md 協作段、`.claude/skills/git-commit/`(碰撞檢查 step)、`.github/workflows/p0.yml`(draft guard)、兩位開發者的日常流程。

## D-020 信用版後台 POM 跨站共用:全同 re-export、有差異 subclass 覆寫

- 狀態:accepted(2026-07-21 nohungry 拍板;graph dedup 掃描後補追認既有演進路線)
- 決策:信用版後台(RC/RE/LT/RD)的 dashboard POM 以 RC 為 base:與 RC 全同的站 **re-export**(LT/RD 現況);有實機差異的站 **subclass RC 並只覆寫差異方法**(RE:Vue tab 需 native click ×2、會員/代理名渲染為 `<a>` 的定位 ×2),差異原因寫進 override docstring。前台 POM 與現金版後台(LU 系)不在本條範圍。
- 理由:RE 原為 RC 整檔複製(388 行),16 個方法中僅 4 個有真差異,其餘 12 個的 drift 全是註解/docstring 失同步 —— 複製模式讓 RC 的修正(如 `_agent_card` tag-agnostic、密碼欄 count 防禦)無法自動到達 RE。subclass 讓共用修正單點生效,差異點顯式可審。
- 替代方案:維持整檔複製(不採:drift 已實際發生);抽獨立共用 base module(不採:RC 即事實上的 base,多一層抽象無收益;`re/login_page.py` docstring 早已預告 subclass 路線)。
- 影響:`pages/dashboard/re/management_page.py`(388→108 行)、後續信用版新站 onboarding 依此模式。

## D-021 Commit message:簡潔英文 subject,細節進 PR body

- 狀態:accepted(2026-07-24 nohungry 提出並拍板)
- 決策:commit subject 一律簡潔英文 `type(scope): summary`(≤72 字元、禁 CJK;types: feat/fix/test/chore/docs/refactor/ci/perf/revert/wip)。細節、理由、`[skip-docs-check] <短理由>` 放 body(第二個 `-m`,語言不限)。PR title 遵守同規則(squash-merge 後即 main 的 commit subject);詳細脈絡寫 PR description。守門:`.github/scripts/check-commit-msg.sh`(PreToolUse hook,違規 block;`SKIP_COMMIT_MSG_CHECK=1` override)。
- 理由:2026-07 中文長 message 把 PR 描述等級的細節塞進 subject,git log 可讀性差、跨工具(blame/shortlog)截斷;英文短 subject + PR 描述承載細節是原有慣例。
- 替代方案:commitlint CI(不採:2 人 repo,hook 層即時擋比 CI 事後紅更有效;必要時再加)。
- 影響:`.claude/settings.json`、`.github/scripts/check-commit-msg.sh`、`git-commit` skill Step 4、CLAUDE.md Git Commit Rules、兩位開發者的 commit 習慣。

## D-022 依賴管理:uv 雙軌制(pyproject+uv.lock 為 source of truth,requirements.txt 為 export 產物)

- 狀態:accepted(2026-07-28 nohungry 拍板)
- 決策:依賴宣告集中在 `pyproject.toml`(`[tool.uv] package = false`,純測試 repo),`uv lock` 產 `uv.lock`(進 git),`uv sync` 管理 `.venv/`(uv 預設 venv 位置即 `.venv/`,既有 `.venv/bin/pytest` 引用全部不變)。`requirements.txt` 改為 `uv export --no-hashes -o requirements.txt` 產出的**全鎖定版**,僅供 pip 相容路徑(CI 的 `pip install -r requirements.txt` 與無 uv 的機器)使用,**禁止手改**。改依賴 SOP:改 pyproject.toml → `uv lock` → `uv export` → 三檔一起 commit。守門 hook + CI 雙保險(`check-docs-sync.sh` deterministic 規則 + `docs-sync-check.yml` 的 `uv-requirements-sync` job,`--frozen` diff)。`.python-version` 鎖 3.10 對齊 CI。
- 理由:本機要 uv 的速度與 lockfile 可重現性,但 CI 與同事機器的 pip 流程不能壞;export 雙軌讓兩條路徑裝出相同版本,順帶修掉「requirements.txt 幾乎無 pin → CI/本機版本漂移」的既有問題。升級依賴從隱性(每次 CI 裝到最新)變顯性(`uv lock --upgrade` + export,diff 可 review)。
- 替代方案:uv 只當安裝器(uv pip install -r requirements.txt;不採:無 lockfile,漂移問題依舊);pip-tools 式 requirements.in→compile(不採:非 uv 原生流,無 uv sync/add 體驗);CI 改用 uv sync(不採本次:降低變更面,pip 路徑保留當相容驗證,未來可再議)。
- 影響:新增 `pyproject.toml`/`uv.lock`/`.python-version`,`requirements.txt` 轉為產物,`check-docs-sync.sh`、`docs-sync-check.yml`、README/CLAUDE.md Setup 段、兩位開發者的依賴變更流程。

## D-023 tests/ 直接 import 站點 POM 由 hook + CI 雙保險擋

- 狀態:accepted(2026-08-08 nohungry 拍板)
- 決策:新增 `.github/scripts/check-factory-import.sh`,採與 `check-docs-sync.sh` 相同的雙模式骨架(PreToolUse hook 檢 staged `tests/**/*.py`;CI 模式掃 `tests/` 全樹,能抓搬檔/改名逃逸)。判定採**例外法**:掃 `tests/` 內所有 `from pages.` 行,**僅字面放行 `from pages.factory import` 與 `from pages.dashboard.factory import`**,其餘一律違規 —— 同時涵蓋前台(D-001)與後台(D-002),**不硬編站點清單**,新增站點零維護。違規:hook exit 2 block、CI job 紅。Override:commit message 含 `[skip-factory-check]`,或 env `SKIP_FACTORY_CHECK=1`。CI job 掛在既有 `.github/workflows/docs-sync-check.yml`(該 workflow 已含與 docs 無關的 `uv-requirements-sync` job,事實上已是「PR 靜態檢查集」;加新 job 不動既有 job 名,不影響任何 required check)。掃描範圍嚴格限於 `tests/**`;`pages/` 內部的跨站 re-export / subclass 是 D-020 核可設計,不在守門範圍。
- 理由:D-001 自 2026-07 追認以來明文禁止,但 2026-08-06 實測 `tests/` 仍有 **62 行 / 42 檔**違規(8 站 `test_p0_smoke.py` 與各站 `feature/visual/*` 幾乎一律違規,lt 站幾乎整站違規),證明純靠紀律與 code review 已失效;同期 `tests/dashboard/` 因無此類歷史包袱維持 0 違規。repo 已有兩個 deterministic 守門的成功前例(`check-docs-sync.sh` D-022、`check-commit-msg.sh` D-021),同骨架擴充成本極低。一次性清理若無守門,違規會再度長回 —— 尤其 LT 換版修復預期會大規模重寫 `tests/lt/`,守門須在修復動工前就位。
- 替代方案:只做一次性清理不加守門(不採:違規是持續回流的,這正是這次要清 62 行的原因);ruff / flake8-tidy-imports `banned-api` 規則(不採:repo 目前無 linter 依賴,D-022 剛把依賴收斂成 uv 雙軌,為單一規則引入 linter 是更大的決策;未來若引入 linter 可再議遷移);conftest 匯入期 assert(不採:只在跑測試時才發現、耗一次 collection,且會誤傷 dev-notes 下合法的一次性 probe 腳本);只掛 CI 不掛 hook(不採:與既有雙保險慣例不一致,Claude 產出的違規要在本機 commit 前就擋);站點清單從 factory registry 動態推導(不採:漏掉 `pages.dashboard.<site>` 的 D-002 型違規,且 bash 讀 python registry 多一層耦合、hook 變慢)。
- 影響:新增 `.github/scripts/check-factory-import.sh`;修改 `.claude/settings.json`(PreToolUse 追加第三支 hook)、`.github/workflows/docs-sync-check.yml`、`CLAUDE.md`(守門段 + Multi-site Factory Pattern 段)、`docs/cicd.md`、`README.md` CI 表;兩位開發者的 commit 流程。

## D-024 Nuxt 前台 POM 不抽共用 base;跨站共用只走 utils 純函式

- 狀態:accepted(2026-08-08 nohungry 拍板)
- 決策:**關閉** 2026-07-21 refactor-audit 的殘項「ks/lg/lu Nuxt HomePage 共用 base」(KS 已於 2026-08-06 PR #167 永久退役,候選縮為 lg/lu)。Nuxt 家族(本 repo 指 qw/lg/lu/rf 這組**前台 POM 結構相近**的站;LT 雖亦為 Nuxt SPA 但 POM 結構自成一格,不屬此家族)的前台 HomePage / LoginPage **不建立共用 base class、不建立 mixin、不做站對站 subclass**。跨站重複只在「與站點 DOM 無關的通用行為」層抽 `utils/` 純函式:本次抽 `utils/game_launch_helper.open_in_new_tab()`(點 launcher → 等新分頁 → maximize)與新增 `utils/menu_helper.leaf_menu_texts()`(選單容器葉節點短文字抽取),兩者皆由呼叫端傳入已定位好的 locator、函式內零站點 selector。**站點導覽語意**(分類入口、nav 點擊、選單開闔、彈窗清理、登入態信號、會員連結)一律 per-site 保留。新 Nuxt 站 onboarding 沿用此邊界。
- 理由:實測(2026-08-06 逐段 diff)只有 LG/LU 的 5 支方法 body 完全相同、差異僅 docstring,合計約 31 行;且相同的部分全是通用 Playwright 行為,不是共用 DOM 契約。qw 的 `open_slots_category` 走 intro-platform tile 且不等 grid、rf 的 `launch_game` 是同分頁路由**回傳 str 而非 Page** —— 契約本質不同,納入 base 會變成 4 站覆寫 3/5,抽象反成負擔。`pages/lu/home_page.py` 檔頭與 `tests/lu/feature/visual/test_visual_regression.py` 皆明載「與姊妹站 LG 差異大,勿照抄」,兩站相同是兩份 Nuxt 樣板偶然收斂而非共同上游(LU sidebar 2026-07-23 改版、LG nav 分類新增,兩站已各自漂移)。且 `utils/game_launch_helper.launch_first_healthy_game` 早已用 duck typing(docstring 明寫「`home` 須提供 open_slots_category / launch_game」)承擔跨站共用,再加類別階層是第二層冗餘抽象。D-020 已對規模大 9 倍的重複(RC/RE dashboard 275 行)判過「抽獨立共用 base module 不採」。
- 替代方案:建 `NuxtHomePageBase` 涵蓋 qw/lg/lu/rf(不採,如上);LU subclass LG(不採:LG 並非事實上的 base,語意錯置;與 D-020 的「RC 即事實 base」情境不同);完全不動、只寫決策關單(不採:兩段通用邏輯抽 utils 成本極低,且讓「新分頁必須 maximize」的踩坑教訓從兩份複製註解變成單點實作)。
- 併記(本次刻意不做,列 backlog):① **base_url 尾斜線正規化四站不一致**(qw 只在 auth_url rstrip、lg/lu/rf 在 `__init__` `rstrip("/") + "/"`、rc/re/rd/lt 完全不處理;`config/settings.py` 的 SiteConfig 不 normalize)—— 實測 repo 內**不存在任何 `site_config.url + "..."` 裸拼接**,所有消費端不是 rstrip 就是 urlparse,goto 本身對尾斜線不敏感,故統一 normalize 是**零風險但也零收益的純 churn**(不是高風險);若未來出現裸拼接需求再議。② **goto 策略不統一**(qw networkidle / lg,lu,rf domcontentloaded+60s / rc,re,rd domcontentloaded + networkidle fallback 8s + dialog dismiss / lt 同型 12s)—— 每一種都是實機踩坑調出來的(見 `pages/rc/login_page.py` goto docstring:dev 站背景 WebSocket 心跳使 load event 常不觸發),統一等於拿穩定度換整齊,**不做**。
- 影響:`pages/lg/home_page.py`、`pages/lu/home_page.py`、`utils/game_launch_helper.py`、新增 `utils/menu_helper.py`、`CLAUDE.md` Architecture utils 區、`README.md` utils 清單;`dev-notes/refactor-audit-2026-07-21.md` §1a 與 §動工結果第 4 項殘項關閉。

## D-025 瀏覽器管道用顯式 BROWSER_MODE 切換,不由 CI 旗標兼差

- 狀態:accepted(2026-08-14 nohungry 拍板)
- 決策:`conftest.py` 新增 `BROWSER_MODE` 環境變數(目前唯一值 `local`)控制「用 Playwright 內建 chromium 直接 launch」;並新增 `_is_launched_browser()`(= CI 或 local)取代原本兩處以 `_is_ci()` 判斷 viewport 策略與 CDP 視窗操作的寫法。判準改為**瀏覽器是不是 launch 出來的**,而非「是否在 CI」。CDP 分支(Windows / WSL / 純 Linux)行為完全不變,**CDP 仍是本機主管道**,`BROWSER_MODE=local` 定位為備援與應急路徑。
- 理由:2026-08-14 Windows 更新(KB5121003 等)重開機後,WSL 網卡被納入 Hyper-V 防火牆(`DefaultInboundAction = Block`),使用者未改任何設定,pytest 的 CDP 9223 與兩個 MCP 的 9224 同時全斷,且傳統 `netsh advfirewall` 規則管不到該層。跨界管道(WSL→Windows)可被 OS 單方面切斷,測試套件需要一條零外部依賴的執行路徑。實測(2026-08-14)前台 RC smoke 8/8 綠、後台 LU login(2FA + 大 bundle)綠,舊有「現金版後台 23MB bundle 在 WSL 內 goto 逾時」的顧慮僅存在於 headless,有頭(WSLg)不成立。
- 替代方案:① 繼續借 `CI=true` 跑本機(不採:語意錯誤——本機不是 CI 環境;且該旗標同時綁死 viewport 策略,兩件事耦合在一個變數上,日後任一方要調整都會誤傷另一方)。② 只修防火牆不加備援(不採:同一類 OS 變更會再發生,且修復需管理員權限,不是每次都能立刻取得)。③ 全面改用 WSL 內建 chromium 取代 CDP(不採:內建 chromium 非 Windows 真 Chrome,與線上使用者實際環境有差異,主管道仍應是真 Chrome)。
- 影響:`conftest.py`(`_use_local_browser` / `_is_launched_browser` / `browser` fixture / `_new_configured_page` / `pytest_configure`)、`.env.example`、`CLAUDE.md` Setup 與 CDP 故障排除段、`README.md` 執行指令與環境對照表、`PORTS_AND_SETUP.md` Step 6(Hyper-V 防火牆排查與修復)。`utils/window_helper.py` 已全程 try/except,兩模式皆安全,不需改。
