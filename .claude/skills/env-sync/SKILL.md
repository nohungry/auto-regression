---
name: env-sync
description: 維持 `.env` 與 `.env.example` 結構同步，並處理同事發放的新 .env 範本合併。當使用者要新增站點 keys、新增/重命名 key、合併同事範本、或編輯 .env / .env.example 任一檔時，使用此 skill。
---

# Purpose

確保專案中三個 env-related 檔案彼此契合：

| 檔案 | Git 狀態 | 角色 |
|------|---------|------|
| `.env` | gitignored | 本機機密，含實際 credentials |
| `.env.example` | tracked | 公開範本，僅含占位符，新進成員的 onboarding 入口 |
| `.env.merged` | gitignored | 暫時性合併工作檔，review 後應併入 `.env` 並刪除 |

**核心契約**：`.env` 動，`.env.example` 必須跟著動（除非只是改 value）。新進成員看 `.env.example` 應能知道「有哪些站、每站需要哪些 keys」。

# Trigger（何時使用此 skill）

主動偵測以下情境並使用：

1. 使用者要**新增站點**（即使只是 `.env` 加 keys，code 端尚未對接）。
2. 使用者要**新增 / 重命名 / 刪除 key**。
3. 使用者收到**同事發放的 .env 範本**（通常在 `/mnt/c/Users/<user>/Downloads/`），要合併到本機。
4. 使用者直接編輯 `.env` 或 `.env.example`。
5. `git status` 出現 `M .env.example` 但本對話未動過它（提醒使用者：是否之前的 .env 變動忘了同步？）。

# Scope rules

1. 此 skill 負責 `.env`、`.env.example`、`.env.merged` 三檔的**結構同步與安全淨化**。
2. 此 skill 不負責 commit／push（交給 `git-commit` skill）。
3. 此 skill 不負責 code 端的新站 onboarding（factory routing / page objects / tests）— 改用 `ui-test-author`。
4. 此 skill 不負責執行測試驗證新 credentials 可用（提醒使用者手動跑 smoke test 驗證）。

# 結構契約（Structure contract）

## 每站 13 keys（必齊全）

| 群組 | Keys | 數量 |
|------|------|------|
| 前台 | `URL`, `USERNAME`, `PASSWORD` | 3 |
| 後台 | `DASHBOARD_URL`, `DASHBOARD_AGENT_URL`, `DASHBOARD_USER`, `DASHBOARD_PASS`, `DASHBOARD_TOTP`, `DASHBOARD_AGENT_USER`, `DASHBOARD_AGENT_PASS` | 7 |
| API | `API_URL`, `API_DOMAIN`, `COMPANYCODE` | 3 |

> `DASHBOARD_URL` = 站長入口（網址含 `-admin`，如 `dev-XX-admin-dashboard`）；
> `DASHBOARD_AGENT_URL` = 代理入口（網址不含 `-admin`，如 `dev-XX-dashboard`），搭配 `DASHBOARD_AGENT_*` 帳號。

每 key 名稱固定為 `SITE_<ID>_<NAME>`，`<ID>` 全大寫站台代號（rc → RC、lt → LT）。

## 站區塊版型

```env
# -----------------------------------------------
# <站名> (<companycode>) — <信用版|現金版>
# -----------------------------------------------
# 前台
SITE_<ID>_URL=...
SITE_<ID>_USERNAME=...
SITE_<ID>_PASSWORD=...
# 後台（站長入口，網址含 -admin）
SITE_<ID>_DASHBOARD_URL=...
# 後台（代理入口，網址不含 -admin）
SITE_<ID>_DASHBOARD_AGENT_URL=...
SITE_<ID>_DASHBOARD_USER=...
SITE_<ID>_DASHBOARD_PASS=...
SITE_<ID>_DASHBOARD_TOTP=...
# 後台（自動化代理帳號，限定權限：管理 + 報表）
SITE_<ID>_DASHBOARD_AGENT_USER=...
SITE_<ID>_DASHBOARD_AGENT_PASS=...
# API
SITE_<ID>_API_URL=...
SITE_<ID>_API_DOMAIN=...
SITE_<ID>_COMPANYCODE=...
```

## 信用版 vs 現金版

兩類站之間以分隔註解區隔：

```env
# =============================================
# 現金版站點（前台密碼規則與信用版不同）
# =============================================
```

**禁止**在分隔註解中寫密碼字面值（任何明文密碼），只寫「規則不同」即可。

# 占位符規則（適用 `.env.example`）

| Key 類型 | 占位符 |
|----------|--------|
| URL | `https://<your-<site>-domain>/` |
| Dashboard URL（站長，-admin）| `https://<your-<site>-admin-dashboard-domain>/` |
| Agent Dashboard URL（代理，無 -admin）| `https://<your-<site>-dashboard-domain>/` |
| API URL | `https://<your-api-domain>` |
| API DOMAIN | `<your-<site>-api-domain>` |
| 一般 user / pass | `your_username` / `your_password` |
| Dashboard user / pass | `your_dashboard_username` / `your_dashboard_password` |
| Agent user / pass | `your_agent_username` / `your_agent_password` |
| TOTP | `your_totp_base32_secret` |
| COMPANYCODE | 保留真實值（如 `drc`、`dlt`，**非機密**） |
| CDP_URL | `http://<WINDOWS_HOST_IP>:9223` |

`DEFAULT_SITE` 對應的站區塊**保持 uncommented**（讓新人 clone 後改占位符即可跑），其他站區塊**整段以 `# ` 註解** 起來（含 keys 與內部註解）。

# 安全紅線（Security guardrails）

執行任何 .env 編輯動作前後，務必檢查：

1. **`.env.example` 不得含真實 credentials**
   - 真實帳號、真實密碼、真實 TOTP secret、真實內網 IP、真實網域 → 一律改占位符
   - `COMPANYCODE` 例外（如 `drc`），因為它就是公開 site code
2. **`.env` 註解中不得含密碼字面值**
   - 例如「後台密碼統一 <明文>」或「前台密碼 <明文>」這類註解，全部改寫成「規則描述」（如「密碼首字大寫，legacy 例外」），不寫明文
3. **真實憑證禁出 `docs/` 與 skill 文件**（見 memory `feedback_no_real_credentials_in_docs.md`）
   - 範例一律用 `xxxx001` / `your_username` 類占位

每次完成 .env 編輯後，跑這條檢查指令並回報結果：

```bash
grep -nE '[Aa]b[0-9]{6}' .env | grep '^[[:digit:]]*:#' || echo "(clean: no password literal in comments)"
```

# CDP_URL 在地化（Critical）

**同事範本的 CDP_URL 永遠不能直接套用**。CDP_URL 是 WSL → Windows host gateway，每台機器（甚至同台 WSL 重啟後）都不同。

**取得當前正確值**：

```bash
ip route show default | awk '{print $3}'
```

**Port 固定 9223**（專案規定，見 memory `feedback_chrome_cdp.md`）。

合併同事範本時，**最後一步**永遠是把 CDP_URL 替換為本機 gateway。

# Workflow

## Pattern A：使用者要新增站點

1. 確認 site_id 與 companycode（多半相同，但有歷史例外，如 RC site_id=`rc` companycode=`drc`）。
2. 判斷信用版／現金版（影響放在哪個分隔區塊之下）。
3. **`.env`**：在對應分隔區塊下加完整 13 keys，填真實 credentials。
4. **`.env.example`**：在相同位置加 13 keys，全部以 `# ` 註解 起來，value 一律占位符。
5. 執行 key 對齊驗證（見「驗證指令」）。
6. 提醒使用者：code 端尚未接（`pages/factory.py` registry、`pages/<site>/`、`tests/<site>/` 均未建），跑該站會 raise ValueError。如需 onboard，引導去 `ui-test-author`。

## Pattern B：使用者要新增 / 重命名 key

1. **每一站都要加／改**（避免漏站造成不對稱）。
2. `.env` 與 `.env.example` 同步動。
3. 若 key 含敏感資訊，`.env.example` 必用占位符。
4. 重命名舊 key → 一併刪除舊 key，避免遺留。

## Pattern C：合併同事發放的 .env 範本

典型流程（依此次 2026-04-30 ~ 2026-05-01 經驗）：

1. **定位來源檔**：通常在 `/mnt/c/Users/<user>/Downloads/env*`，問清楚是哪份。
2. **Key 比對**（用本檔「驗證指令」），確認新範本與現有 `.env` keys 是否一致。
   - 若新範本多 key → 通常是新增站／新增 key
   - 若新範本少 key → 確認同事是否漏寫，或要刪 key
3. **Value 差異列表**：用 `diff` 列出每個 key value 不同處，**逐項給使用者裁示**（特別是大小寫、URL 路徑、帳號改名）。
4. **生中間檔 `.env.merged`**（不要直接覆蓋 `.env`）：
   ```bash
   cp <teammate-template> .env.merged
   ```
5. **CDP_URL 在地化**：把 `.env.merged` 的 CDP_URL 改回本機 gateway。
6. **註解去敏感化**：移除所有含密碼字面值的註解。
7. **內部一致性檢查**：例如「開頭規則註解寫 admin URL，但區塊 value 寫非 admin URL」這種同檔內衝突，務必揪出並請使用者裁示。
8. **使用者 review `.env.merged` 通過後**：
   ```bash
   cp .env /tmp/.env.backup-$(date +%Y%m%d-%H%M%S)  # 一定要先備份
   cp .env.merged .env
   rm .env.merged                                     # 避免兩份重複
   ```
9. **`.env.example` 同步**：若範本帶來新站／新 key，按 Pattern A/B 同步 `.env.example`。
10. **記憶更新**：若帳號命名規則有 quirk（典型：legacy 命名、typo），加入或更新對應 project memory。

## Pattern D：使用者直接編輯 .env / .env.example 其中一檔

1. 編輯後立刻檢查另一檔是否需要同步。
2. 跑驗證指令確認 key 對齊。

# 驗證指令（每次編修完都跑）

## 1. Key 對齊檢查

```bash
# 萃取 .env 與 .env.example 的所有 key 名（含被註解的站區塊也要算）
grep -oE '^[# ]*[A-Z][A-Z0-9_]+=' .env | sed 's/^# *//' | sort -u > /tmp/keys_env.txt
grep -oE '^[# ]*[A-Z][A-Z0-9_]+=' .env.example | sed 's/^# *//' | sort -u > /tmp/keys_example.txt
echo "=== Only in .env ==="; comm -23 /tmp/keys_env.txt /tmp/keys_example.txt
echo "=== Only in .env.example ==="; comm -13 /tmp/keys_env.txt /tmp/keys_example.txt
echo "=== Common: $(comm -12 /tmp/keys_env.txt /tmp/keys_example.txt | wc -l) ==="
```

兩個 "Only in" 區塊都應該是空的。

## 2. 密碼字面值檢查

```bash
grep -nE '[Aa]b[0-9]{6}' .env | grep '^[[:digit:]]*:#' && echo "❌ password literal in comments" || echo "✅ clean"
grep -nE '[Aa]b[0-9]{6}' .env.example && echo "❌ real password in example" || echo "✅ clean"
```

## 3. 站數一致

```bash
# 用 SITE_<ID>_URL 當錨點（每站一個）
echo ".env 站數: $(grep -cE '^SITE_[A-Z]+_URL=' .env)"
echo ".env.example 站數（含註解）: $(grep -cE '^# *SITE_[A-Z]+_URL=' .env.example | head; grep -cE '^SITE_[A-Z]+_URL=' .env.example)"
```

# 已知 quirks（站台命名歷史例外）

合併或檢查時若遇到以下值，**保持原樣不要自動「修正」**：

> ⚠️ 實際帳密值一律以本機 `.env` 為準，本表只描述「規則差異」不寫真實值（依 [[feedback-no-real-credentials-in-docs]]）。

| 站 | Key | quirk（規則，非實際值） | 原因 |
|----|-----|------------------------|------|
| RC | `SITE_RC_DASHBOARD_AGENT_USER` | 沿用 legacy 命名，**不**符合標準 `qaauto<site>` 樣式 | 第一組創建，未跟著改名 → 不要自動「修正」成標準樣式 |
| RC | `SITE_RC_PASSWORD` / `SITE_RC_DASHBOARD_PASS` | 密碼**首字大寫**（其他信用版站皆全小寫） | Legacy 帳號平台未統一更新 → 不要自動改成小寫 |
| RE | `SITE_RE_DASHBOARD_AGENT_USER` | 帳號尾字少一個 `t`（typo） | 創建時 typo，**不要**自動補字 |
| LT | `SITE_LT_DASHBOARD_AGENT_USER` | 曾於 2026-04-30 改名統一為標準樣式 | 與舊命名不同，以 .env 現值為準 |
| 其他 | `SITE_<X>_DASHBOARD_AGENT_USER` | 標準命名樣式 `qaauto<site>`（site 小寫） | 一般規則 |

# 與其他 skill 的銜接

| 完成後可能下一步 | 對應 skill |
|------------------|-----------|
| 把 `.env.example` 改動 commit / 開 PR | `git-commit` |
| 為新增站點建 page object 與 tests | `ui-test-author`、`pom-architect` |
| Review .env.example 改動是否合理 | `test-review`（廣義 review） |

# 不要做（Anti-patterns）

1. **不要直接覆蓋 `.env`** — 一律走 `.env.merged` 中間檔 + 備份 + review。
2. **不要把同事範本的 CDP_URL 直接套到本機**。
3. **不要在 `.env.example` 留任何真實 credential**（即使覺得「只是 dev 環境」）。
4. **不要在 `.env` 註解寫密碼字面值**（密碼規則描述可以，字面值不行）。
5. **不要為了「修正」而改動已知 quirks**（RC 大寫、RE typo 等）— 改動前必先跟使用者確認。
6. **不要假設 `.env` 變動 = code 接好**。新增站 keys 後，`pages/factory.py` 不會自動知道；該站任何測試會 raise ValueError。
