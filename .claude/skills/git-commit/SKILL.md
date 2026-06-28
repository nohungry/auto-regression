---
name: git-commit
description: 針對 auto-regression repo 的測試變更，執行提交前檢查、整理 diff、建議驗證步驟與 commit message。當使用者準備 commit、要求整理變更摘要、或需要提交前品質把關時，使用此 skill。
---

# Purpose
用於此 repo 的提交前整理工作，包含：
- 摘要測試相關變更內容。
- 依改動範圍建議最小必要驗證指令。
- 檢查是否混入高風險或無關修改。
- 產出清楚的 commit message 候選。
- 確保提交內容適合當前與未來 multi-site 擴充。

# Repo context
- 技術棧：Python + pytest-playwright。
- 測試位於 `tests/<site_id>/`，page objects 位於 `pages/<site_id>/`。
- `pages/factory.py` 使用 registry dict 做 multi-site routing。
- 每站有自己的 `tests/<site_id>/conftest.py`，覆寫 `site_config` 與站台特定 fixture。
- visual regression baseline 依既有 snapshot 結構管理，動態頁參考圖位於 `screenshots/<site_id>/vr_reference/`。
- 截圖系統 `utils/screenshot_helper.py` 自動產出 `screenshots/<site_id>/<timestamp>/<test_name>/README.md`，為 auto-generated 不需 commit。
- pytest 執行路徑一律使用 `.venv/bin/pytest`。
- **任何 commit / push 動作需先經使用者確認**，不可自行執行。
- **禁止在 `main` 分支上直接開發 / commit / push**。`main` 只接受 PR merge，所有修改必須開 feature branch（例如 `feat/xxx`、`fix/xxx`、`refactor/xxx`），push 後開 PR 審核合併。
- Git commit 禁止包含 `Co-Authored-By: Claude` 行。

# Pre-commit workflow

## Step -1 — 分支檢查（最先做，在 Step 0 之前）

**硬規**：不得在 `main` 上 commit / push。流程：

1. `git branch --show-current` 確認目前分支。
2. 若目前在 `main`：
   - 若尚未 commit（只有 working tree 變動）：請使用者/自動 `git switch -c <feature-branch>` 建立新分支再走 Step 0+。分支命名：`feat/xxx`、`fix/xxx`、`refactor/xxx`、`chore/xxx`。
   - 若已誤 commit 在 main：停止 push，提議 rescue 流程：
     ```
     git switch -c <feature-branch>       # 把 commits 帶到新分支
     git switch main
     git reset --hard origin/main         # main 回到乾淨狀態（destructive，需使用者確認）
     git switch <feature-branch>
     ```
     `git reset --hard` 為破壞性操作，**必須先取得使用者確認**再執行。
3. 確認在非 main 分支後，才進入 Step 0。

## Step 0 — Credential / Secret scan（最高優先，必做）

**在做任何其他檢查之前，先掃描 diff 確認沒有任何帳號、密碼、token、API key 被硬寫進 code。所有認證資訊必須完全由 `.env` 控制。**

1. 取得完整 diff：`git diff --staged` + `git diff`（未 staged 也要掃，避免使用者稍後 `git add .`）。
2. 若使用者還沒 stage，先用 `git status` + `git diff` 看所有有差異的檔案。
3. 對每一個新增或修改的行（`+` 開頭），逐條比對下列可疑模式：

   | 類型 | 可疑模式 | 例外（允許） |
   |------|---------|-------------|
   | 密碼 literal | `password = "xxx"`、`passwd=`、`pwd=`、`PASSWORD:` 後面接明文 | `os.getenv("SITE_*_PASSWORD")`、`site_config.password` |
   | 帳號 literal | `username = "xxx"`、`user = "norman001"`、`account = "dlttest01"` 等已知測試帳號字串 | `os.getenv(...)`、`site_config.username`、fixture 取值 |
   | Token / Key | `token = "..."`、`api_key = "..."`、`secret = "..."`、`Bearer xxxxx`、`sk-`、`ghp_`、`AIza` 開頭字串 | `os.getenv(...)`、從 config/fixture 注入 |
   | TOTP secret | Base32 字串（大寫字母 + 2-7，16/32 字元長） | `site_config.dashboard_totp` |
   | URL 帶認證 | `https://user:pass@host/...` | 無 |
   | Cookie / Session | `Cookie: sessionid=...`、硬寫 JWT（`eyJ...`） | 從 response 動態取得 |
   | Connection string | `mongodb://user:pass@`、`mysql://user:pass@`、`postgres://...` | 無 |

4. 已知測試帳號名單（出現即為紅旗，除非在 `.env.example` 的示例或註解中）：
   - 各站測試帳號（格式範例：`xxxx001`、`xxxxtest01` 這類英文 + 數字組合）— 實際值請對照 `.env` 中 `SITE_*_USERNAME`
   - Dashboard：任何 `SITE_*_DASHBOARD_USER` 對應值
   - 其他：任何看起來像使用者/測試員的英文 + 數字組合字串

5. 檢查 `.env.example` 本身：只能有 key 與**空值**或**明顯佔位字元**（如 `your_password_here`、`xxx`、`<FILL_ME>`），不能有真實密碼。

6. 檢查 .env 本身是否**意外**被 stage：`git diff --staged --name-only | grep -E '^\.env$'` 必須為空。

7. 若發現任何疑似 credential：
   - **立刻停止 commit 流程**，不產生 commit message。
   - 明確列出檔案、行號、可疑字串（密碼值只顯示前 2 字 + `***`，不要完整輸出到 log）。
   - 建議的修復方式：移到 `.env`（並更新 `.env.example` 的 key，不含值）+ 透過 `config/settings.py` 的 `SiteConfig` 讀取 + 測試中透過 fixture 取用。
   - 若是既有硬寫值要移除，提醒使用者**git history 可能仍殘留**，若密碼已洩漏需要實際更換而非僅移除程式碼。

8. **Repo-wide 既有內容掃描（每次 commit 觸及 docs/ 或 .claude/skills/ 時必做）**：
   diff-only 掃描會漏掉「過去 PR 已混入、本次未動」的真實憑證。當本次變更含 `docs/**` 或
   `.claude/skills/**` 時，額外對**全 tracked 檔**（排除 `.env`、`*.png`）跑一次：
   ```bash
   # 真實密碼 / TOTP secret（最危險）
   git grep -nE '[Aa]b[0-9]{6}' -- ':!.env' ':!*.png'
   git grep -nE '[A-Z2-7]{26,}' -- ':!.env' ':!*.png' | grep -vE 'http|README|[a-z]'
   # 真實測試帳號名（docs/skill/註解禁寫，見 feedback_no_real_credentials_in_docs）
   git grep -nE '<已知測試帳號樣式，如 站碼auto[0-9]+ / qaauto站碼>' -- ':!.env'
   ```
   命中既有真實值 → 一併清理（改佔位 + 指向 `.env`），不因「不是本次加的」而放行。
   密碼/secret 命中時提醒：**git history 已殘留，需實際更換憑證**而非僅改文字。

9. 若掃描乾淨，才進入 Step 1。

## Step 1 — 變更分類

1. 先摘要變更檔案，依類型分類：

   | 分類 | 路徑 | 風險等級 |
   |------|------|---------|
   | tests | `tests/<site_id>/*.py` | 中 — 只影響對應站點 |
   | pages | `pages/<site_id>/*.py` | 中 — 可能影響該站所有測試 |
   | factory | `pages/factory.py` | **高** — 影響所有站點路由 |
   | conftest（全域） | `conftest.py` | **高** — 影響所有站點 fixture |
   | conftest（站點） | `tests/<site_id>/conftest.py` | 中 — 只影響該站 fixture 覆寫 |
   | utils | `utils/*.py` | **高** — 跨站共用 |
   | config | `config/settings.py` | **高** — 影響所有站點設定讀取 |
   | snapshots (legacy) | `tests/lt/__snapshots__/` | 低 — 舊 baseline，目前無測試引用；如有改動需說明保留或刪除理由 |
   | VR reference | `tests/lt/feature/visual/` + `screenshots/lt/vr_reference/`（輸出不 commit） | 中 — 改動 capture 邏輯需說明 |
   | screenshots | `screenshots/` | 低 — auto-generated，通常在 .gitignore |
   | pytest.ini | `pytest.ini` | 中 — marker 與 addopts 變更影響執行行為 |

2. 判斷此次修改屬於哪一類：
   - **testcase authoring**：新增/修改測試案例
   - **page object refactor**：重構 POM 方法或 selector
   - **fixture/infra change**：conftest、factory、utils 調整
   - **visual regression update**：snapshot baseline 或 mask 邏輯變更
   - **new site onboarding**：新站點導入

3. 根據修改範圍，提出最小必要驗證指令。
4. 若使用者已執行過測試，整理結果；若尚未執行，提醒至少先跑 targeted pytest。
5. 檢查此次變更是否把站點名稱、站點目錄或規則不必要地寫死。

## Step 2 — CDP 本地實際測試驗證（腳本類變更必做，非腳本類略過）

**規則**：任何屬於「腳本類」的變更，都必須**在本地透過 CDP 實跑通過**後才能 commit。非腳本類（純文件 / 結構調整 / 設定檔 / .md）則略過此步。

### 2.1 判斷是否屬於「腳本類」

必須跑 CDP 驗證 ✅：

| 變更類型 | 路徑 | 原因 |
|---------|------|------|
| 新增 / 修改 test 案例 | `tests/<site_id>/**/*.py`（非 `__init__.py`） | 改到測試邏輯本身 |
| POM 方法變動 | `pages/<site_id>/**/*.py` | 測試會呼叫到 |
| Fixture / infra | `conftest.py`、`tests/<site_id>/conftest.py`、`pages/factory.py` | 影響所有測試執行 |
| 共用 utils | `utils/*.py`（除非純註解） | 跨測試共用 |
| pytest 執行設定 | `pytest.ini` 的 `addopts` / plugin / collection 行為變動 | 改變執行流程 |
| 站點設定讀取 | `config/settings.py` 邏輯變動 | 影響所有站點 |

可略過 CDP 驗證 ❌：

| 變更類型 | 路徑 | 原因 |
|---------|------|------|
| 文件 | `CLAUDE.md`、`docs/**/*.md`、`dev-notes/**/*.md`、`.claude/skills/**/*.md`、模組內純 docstring 調整 | 不影響執行 |
| 設定 / 樣板 | `.env.example`、`.gitignore`、`.gitattributes`、`pytest.ini` 只改 marker 註冊 | 不改邏輯 |
| 結構調整 | 檔案 rename / move（內容不變）、目錄重組 | 行為等價 |
| auto-generated | `screenshots/**`（正常應在 gitignore 內不該 stage） | 非腳本 |
| API 測試內文不變、只動 marker | `tests/api/**/*.py` 僅增 `@pytest.mark.xx` | 不影響實際執行路徑 — 但建議仍跑一次確認 marker 語法正確 |

**灰色地帶**（偏保守）：
- `requirements.txt` 改動：若新增 / 升級 playwright / pytest 主要依賴 → 跑；僅加輔助套件 → 可略。
- Pure 註解 / docstring 調整在 `.py` 檔內：嚴格說算腳本類，但若 diff 只有註解可略。判斷原則：**`git diff` 濾掉註解後還有程式變動嗎？有 → 跑；沒 → 略**。

### 2.2 CDP 實跑流程

前提：`.env` 已設定 `CDP_URL`（WSL 連 Windows Chrome），且 Chrome 已開啟 remote debug（見 `feedback_chrome_cdp.md` memory）。

| 變更範圍 | 必跑指令（CDP 本地） |
|---------|---------------------|
| 前台單站單檔（`tests/<site_id>/<file>.py`） | `.venv/bin/pytest tests/<site_id>/<file>.py -v` |
| 前台單站 POM（`pages/<site_id>/`） | `.venv/bin/pytest tests/<site_id>/ -v` |
| 前台單站 conftest | `.venv/bin/pytest tests/<site_id>/ -v` |
| 後台單站單檔（`tests/dashboard/<site_id>/<file>.py`） | `.venv/bin/pytest tests/dashboard/<site_id>/<file>.py -v` |
| 後台單站 POM（`pages/dashboard/<site_id>/`） | `.venv/bin/pytest tests/dashboard/<site_id>/ -v` |
| 後台單站 conftest | `.venv/bin/pytest tests/dashboard/<site_id>/ -v` |
| API 單站（`tests/api/<site_id>/`） | `.venv/bin/pytest tests/api/<site_id>/ -v` |
| `pages/factory.py`（前台） | `.venv/bin/pytest tests/ -v --ignore=tests/dashboard --ignore=tests/api`（所有已註冊前台站點） |
| `pages/dashboard/factory.py`（後台） | `.venv/bin/pytest tests/dashboard/ -v`（所有已註冊後台站點） |
| 全域 `conftest.py` / `utils/*.py` / `config/settings.py` | `.venv/bin/pytest -v`（全量） |
| VR baseline / reference 變動 | `.venv/bin/pytest -m visual_regression -v` |

### 2.3 驗證確認方式

**預設由 Claude 執行 CDP 驗證**，不要求使用者自行跑。不得以 type check / 語法檢查代替實跑。流程：

1. **Claude 執行 CDP 驗證（預設）**：
   - 先確認 `.env` 的 `CDP_URL` 可連（`curl -s -o /dev/null -w "%{http_code}" "$CDP_URL/json/version"` 應回 200）。
   - 確認 `.venv/bin/pytest` 存在可執行。
   - 依 Step 2.2 的「變更範圍 → 指令」對照表跑對應測試，使用 `--tb=short` 節省輸出，必要時 `| tail -N` 只看末段摘要。
   - Bash 工具的 `timeout` 依預期跑多久設（smoke ~6 min、全量 ~20 min，設 `timeout: 600000` 上限）。
   - 跑完把結果摘要回報給使用者（passed/failed/errored 計數 + 任何錯誤訊息）。

2. **單帳號併發防呆**：依 memory `feedback_single_session_per_account.md`，同帳號不可同時跑兩個 pytest process。若使用者當下正在跑其他測試，**先等完再跑**；不可並行。

3. **使用者本地已跑的情境**（偶發）：若使用者明確說「我剛跑過了」並貼出結果，則採信其結果；否則預設仍由 Claude 重跑驗證。

4. **若任何相關 test `failed` 或 `errored`**：**停止 commit 流程**，回報錯誤與可能原因，要求先修復（或拆 commit 只 commit 已通過的部分）。不得隱藏失敗直接 commit。

5. **若 test 被 `skipped`**：判斷是否為合理（例如 LT 改版中 skipped）或需要修復，回報給使用者確認。

### 2.4 違反此規則的紅旗

- 腳本類變更但使用者說「直接 commit 不跑」→ **拒絕生 commit message**，要求先跑或明確授權略過並說明理由（例如 infra 問題無法本地跑，會在 CI 補）。
- 跑的範圍小於實際變更影響範圍（例如改了 `utils/*.py` 卻只跑單一站點）→ 提醒擴大範圍。
- 測試跑完有 fail 卻仍要 commit → 拒絕，要求拆 commit 或修復。

## Step 3 — 文件同步檢查（每次 commit 都做）

**規則**：每次 commit 前，**逐項對照 `CLAUDE.md` 的「文檔維護對照表（code 變動 → 要同步的 doc）」**（文檔同步的唯一 source of truth），判斷此次變更是否影響任何 `.md` 文件的正確性。若有，先更新文件再 commit（或至少提醒使用者）。下表為對照表的本地展開，**內容以 CLAUDE.md 為準**。

### 3.1 文件位置清單

| 文件 | 覆蓋範圍 | 觸發更新條件 |
|------|---------|-------------|
| **`README.md`（repo 根，第一公民）** | **對外總覽：站台表 / 測試數 / 目錄樹 / 執行指令 / markers 表 / 文件資源** | **新站點、新 marker、新 util、CI 變動、新 docs 檔 — 最容易被漏的就是這份** |
| `CLAUDE.md`（repo 根） | 架構、fixtures、markers、慣例、站點清單、文檔維護對照表 | POM 結構變、新 fixture、新 marker、新站點、慣例規則調整 |
| `docs/**/*.md` | 團隊共享知識 | 測試策略、文案對照、API 契約、onboarding 指南變動 |
| `dev-notes/README.md` | 個人筆記目錄說明 | 目錄分類原則變動（其他 dev-notes 檔案 gitignored，**不算可抵免文檔義務的對象**） |
| `.claude/skills/<skill>/SKILL.md` | 對應 skill 本身的規則 | skill 涵蓋流程改變（例如 git-commit skill 新增 step） |
| `README.md`（子目錄，如 `docs/README.md`） | 該目錄用途說明 / 索引 | 該目錄結構、用途或檔案清單變動 |
| POM / test 模組 docstring | 該檔用途與注意事項 | 該檔 public API 變動、站點差異註記變動 |
| `.env.example` | env 變數清單與用途 | 新增 / 改名 / 刪除 env key |

### 3.2 判斷流程

針對本次 diff，逐項檢查：

1. **新增 / 修改 fixture** → `CLAUDE.md` 的 Fixtures section 是否需要加該 fixture 的說明？
2. **新增 pytest marker** → `CLAUDE.md` Markers list + `pytest.ini` `markers` 是否同步？
3. **新增站點目錄** → `CLAUDE.md` Architecture 樹狀圖、站點清單、factory pattern section 是否加入？
4. **POM public method 重命名 / 簽名變動** → 該 POM 檔的 docstring + `CLAUDE.md` 若有提到該方法，需同步。
5. **慣例變動**（如新增 selector 規則、截圖規則、互動例外）→ `CLAUDE.md` Coding Conventions section 需同步。
6. **截圖系統 / VR 流程變動** → `CLAUDE.md` 相關 section + `docs/` 若有對應專文。
7. **新增 / 改名 env key** → `.env.example` 必更新；`CLAUDE.md` Setup section 若有列 key 也需同步。
8. **skill 規則變動** → 對應 `SKILL.md` 更新；若影響 skill 之間的分工邊界，另一個 skill 的描述也要同步。
9. **測試策略 / 覆蓋邊界變動**（例如 P0 smoke 範圍重新定義）→ `docs/` 測試策略文 + `CLAUDE.md` Test Strategy 表格。
10. **檔案 rename / move** → 任何 `.md` 中引用該路徑的段落需同步（grep `.md` 找舊路徑）。

### 3.3 Claude 的具體動作

1. 對每個 diff 條目，逐項檢查上列 3.2，列出「可能需要同步的文件」清單。
2. 若確定需要更新：**在 commit 前完成文件更新**，併入同一個 commit，或明確拆兩個 commit（先改 code，再改 doc）讓使用者選。
3. 若不確定：列出疑問清單給使用者決定。
4. 文件更新完成後，一併納入 Step 2 的 CDP 驗證（只有腳本有改才需要跑；純 .md 更新不需要跑）。
5. 若使用者明確拒絕更新文件，記錄在 commit message body 說明「doc intentionally deferred」並建議補 follow-up issue。

### 3.4 常見遺漏模式

- 新增站點但忘了更新 `CLAUDE.md` 的 `tests/<site_id>/` 目錄清單。
- 改了 fixture 簽名但 `CLAUDE.md` Fixtures section 還列舊簽名。
- 新增 marker 只改 `pytest.ini` 忘了 `CLAUDE.md` Markers list。
- skill 流程新增 step 但 skill 的 `description` frontmatter 未更新。
- 移除 test 檔但 `CLAUDE.md` Architecture 樹狀圖還列著。

## Step 4 — 產出建議 commit message

（原有 Step 6，移到最後）

# Validation rules — 最小必要驗證
依變更範圍遞增：

| 變更範圍 | 建議驗證指令 |
|----------|-------------|
| 前台單站單檔（`tests/<site_id>/<file>.py`） | `.venv/bin/pytest tests/<site_id>/<file>.py -v` |
| 前台單站 page object（`pages/<site_id>/`） | `.venv/bin/pytest tests/<site_id>/ -v` |
| 前台單站 conftest | `.venv/bin/pytest tests/<site_id>/ -v` |
| 後台單站單檔（`tests/dashboard/<site_id>/<file>.py`） | `.venv/bin/pytest tests/dashboard/<site_id>/<file>.py -v` |
| 後台單站 page object（`pages/dashboard/<site_id>/`） | `.venv/bin/pytest tests/dashboard/<site_id>/ -v` |
| 後台單站 conftest | `.venv/bin/pytest tests/dashboard/<site_id>/ -v` |
| API 單站（`tests/api/<site_id>/`） | `.venv/bin/pytest tests/api/<site_id>/ -v` |
| factory.py（前台） | `.venv/bin/pytest tests/ -v --ignore=tests/dashboard --ignore=tests/api`（所有已註冊前台站點） |
| dashboard/factory.py（後台） | `.venv/bin/pytest tests/dashboard/ -v`（所有已註冊後台站點） |
| 全域 conftest.py | `.venv/bin/pytest -v`（全量） |
| utils/*.py | `.venv/bin/pytest -v`（全量） |
| visual regression baseline | `.venv/bin/pytest -m visual_regression -v` |
| 新站點導入（前台） | `.venv/bin/pytest tests/<new_site_id>/ -v` + 確認 factory 註冊 |
| 新站點導入（後台） | `.venv/bin/pytest tests/dashboard/<new_site_id>/ -v` + 確認 dashboard factory 兩 registry 都註冊 |

其他規則：
1. 若修改 visual regression baseline 或 reference screenshot，必須要求說明變更原因。
2. 若測試未執行，不應假裝已驗證通過。
3. 若 diff 同時含重構與功能修補，需提醒使用者確認是否要拆 commit。
4. 若變更涉及新增站點，需確認是否完整走完 onboarding checklist。

# Diff review — red flags
review diff 時注意以下紅旗：
1. 混入無關檔案（例如 `.env`、IDE 設定檔）。
2. snapshot 更新但缺乏變更原因說明。
3. 新增裸 `time.sleep()` 或 debug 用的 `print()`/`breakpoint()`。
4. 不必要的大量 formatting 修改（與功能變更混在一起）。
5. page object public API 簽名變更（影響 conftest fixture）。
6. 特定站點名稱硬寫進本應共用的規則或 helper。
7. 直接 `from pages.<site_id>.xxx import` 出現在 test 中而不走 factory。
8. factory.py 的 registry 中新增了站點，但缺少對應的 `pages/<site_id>/` 或 `tests/<site_id>/conftest.py`。
9. `screenshots/` 目錄下的 auto-generated 檔案被 commit（應在 .gitignore）。
10. commit message 含 `Co-Authored-By: Claude` 行。
11. 腳本類變更（見 Step 2.1）卻無 CDP 本地實跑紀錄 — 違反硬性規則。
12. diff 含腳本 API / fixture / marker / 站點結構變動，但 `CLAUDE.md` / `docs/` / `.env.example` 等對應文件未同步更新。**特別檢查：新站點、新 marker 是否漏改 root `README.md`（最常見漏更新；docs-sync hook 對這兩類有硬規則會 block）；是否用不相關 / `dev-notes/` 的 `.md` 蒙混過檢查。**
13. 目前分支是 `main` — 禁止在 main 上 commit / push（見 Step -1）。

# Commit message rules
1. 使用動詞開頭，說明意圖，而不是只列檔名。
2. 格式：`<type>(<scope>): <description>`
   - type：`feat`（新測試/新站點）、`fix`（修正）、`refactor`（重構）、`chore`（設定/infra）
   - scope：站點 id 或 `shared`/`infra`
   - 例如：`feat(lt): add locale visual matrix smoke tests`
   - 例如：`refactor(shared): migrate factory.py to registry pattern`
   - 例如：`fix(rc): stabilize login loading wait with explicit timeout`
3. 若變更含 refactor + test fix，可用單一主題整合，但需保持語意清楚。
4. commit message 應能讓 reviewer 從 git log 快速判斷風險。
5. 若包含 snapshot 變更，訊息中明確點出 visual regression 調整。
6. 若包含新站點導入，訊息中明確指出對應 `site_id` 與目錄結構。
7. 禁止包含 `Co-Authored-By: Claude` 或任何 Claude co-author 行。

# New site onboarding — commit 前確認
若此次 commit 包含新站點導入，檢查以下項目是否齊全：
- [ ] `.env` 已新增 `SITE_<ID>_URL`/`USERNAME`/`PASSWORD`（不 commit .env，但需確認 .env.example 或文件有更新）
- [ ] `pages/<site_id>/` 目錄已建立，含 `__init__.py`、`login_page.py`、`home_page.py`
- [ ] `pages/factory.py` registry 已新增該站的 LoginPage 與 HomePage
- [ ] `tests/<site_id>/` 目錄已建立，含 `__init__.py`、`conftest.py`、至少一個 test 檔
- [ ] `tests/<site_id>/conftest.py` 至少覆寫了 `site_config`
- [ ] 已評估全域 `page` fixture 的 MutationObserver 注入是否需覆寫
- [ ] `pytest.ini` 若有新 marker 已宣告
- [ ] `CLAUDE.md` Architecture 區塊已更新

# Output expectations
完成任務時，應：
- 摘要本次變更檔案，標示風險等級。
- **標示本次是否包含腳本類變更**（Step 2.1 判斷）；若有，列出對應的 CDP 必跑指令，並確認使用者本地已跑通過 — 未跑不得產生 commit message。
- **列出可能需要同步的文件清單**（Step 3.2 逐項檢查）；若有，在 commit 前完成文件更新或明確說明拆 commit 策略。
- 列出建議先執行的 pytest 指令（重申範圍）。
- 指出是否適合直接 commit，或應先補驗證 / 補文件。
- 若有 diff red flags（特別含 #11 無 CDP 實跑 / #12 文件未同步），逐條列出。
- 若有 multi-site 擴展性問題，先提醒。
- 提供 1~3 個 commit message 候選，遵循 `type(scope): description` 格式。
