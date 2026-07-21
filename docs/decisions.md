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
- 決策:t9platform 信用版後台(RC/RE/LT/RD)的 dashboard POM 以 RC 為 base:與 RC 全同的站 **re-export**(LT/RD 現況);有實機差異的站 **subclass RC 並只覆寫差異方法**(RE:Vue tab 需 native click ×2、會員/代理名渲染為 `<a>` 的定位 ×2),差異原因寫進 override docstring。前台 POM 與現金版後台(LU 系)不在本條範圍。
- 理由:RE 原為 RC 整檔複製(388 行),16 個方法中僅 4 個有真差異,其餘 12 個的 drift 全是註解/docstring 失同步 —— 複製模式讓 RC 的修正(如 `_agent_card` tag-agnostic、密碼欄 count 防禦)無法自動到達 RE。subclass 讓共用修正單點生效,差異點顯式可審。
- 替代方案:維持整檔複製(不採:drift 已實際發生);抽獨立共用 base module(不採:RC 即事實上的 base,多一層抽象無收益;`re/login_page.py` docstring 早已預告 subclass 路線)。
- 影響:`pages/dashboard/re/management_page.py`(388→108 行)、後續信用版新站 onboarding 依此模式。
