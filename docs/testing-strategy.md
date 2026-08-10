# 測試策略與執行規範

> 最後更新：2026-07-24
> 適用範圍：`tests/` 全部（RC、LT、API、Dashboard）

本文件定義測試套件的分層、通過標準、與執行規範。實作腳本與 CI/CD 細節另見 `dev-notes/regression-strategy.md`（目前為規劃階段）。

---

## 測試分層（Level）

| 層級 | 範圍 | 目標耗時 | 目的 |
|------|------|---------|------|
| **L0 Sanity** | API 健康度 + 單站 smoke 核心 3 項 | < 2 分鐘 | 快速驗證環境與後端活著 |
| **L1 Smoke** | 各站 P0 smoke 全跑（rc/lt/re/rd） | ~10 分鐘 | 核心流程健康度 |
| **L2 Feature** | 各站 P1 feature 全跑 | ~45 分鐘 | 功能層回歸 |
| **L3 Full** | L1 + L2 + API 全部 | ~56 分鐘 | 完整回歸 |

> 各層應可獨立執行（透過 pytest marker 或路徑篩選）。

---

## 觸發時機對應

| 觸發時機 | 建議層級 | 說明 |
|---------|---------|------|
| 每日（工作日） | L1 Smoke | 確認環境與核心流程正常 |
| 前端部署後 | L3 Full | 確認無 regression |
| 後端 API 變更後 | API only | 快速驗證契約未破壞 |
| Release 前 | L3 Full × 2 | 連續通過才放行（防 flaky） |
| Hotfix 後 | L0 Sanity | 快速確認修復有效且核心沒壞 |
| 新站點上線 | 該站 Full | 單站完整驗證 |

---

## 通過標準（Pass Criteria）

| 層級 | 標準 | 不通過處理 |
|------|------|-----------|
| L0 Sanity | 0 fail | 立即通知，阻擋部署 |
| L1 Smoke | 0 fail | 立即通知，調查原因，阻擋部署 |
| L2 Feature | 0 fail，skip 需有對應 issue | fail 項建 ticket 追蹤，不阻擋但需排期修復 |
| L3 Full | Smoke 0 fail + Feature fail ≤ 3 | Smoke fail = 阻擋；Feature fail > 3 = 阻擋 |
| Release | 連續 2 次 L3 Full = 0 fail | 任一次有 fail 則重跑，持續 fail 則不放行 |

---

## Flaky Test 處理原則

1. **首次 fail**：確認是產品問題還是測試問題
2. **環境問題**（timeout、CDP 斷線）：重跑一次，仍 fail 則記錄環境問題
3. **確認 flaky**：標記 `@pytest.mark.flaky`（需新增 marker），附 issue link
4. **連續 3 次 flaky**：必須修復或暫時 skip（附原因）
5. **Skip 的測試**：每月 review，超過 30 天未處理的 skip 必須決定修復或刪除

---

## 並行執行限制

| 規則 | 原因 |
|------|------|
| **同帳號不可並行**（含 API + UI 並行） | 後端「從其他裝置登入」機制會互踢 session，回傳 HTTP 401 PermissionDenied |
| **不同站台可並行** | rc/lt/re/rd 各用獨立帳號，彼此不衝突 |
| **API 可獨立並行** | 不依賴瀏覽器，但仍受同帳號規則限制 |

---

## 測試資料管理

| 類型 | 現況 | 規範 |
|------|------|------|
| 測試帳號 | 各站固定測試帳號（實際帳密見 `.env` 的 `SITE_<X>_USERNAME` / `SITE_<X>_PASSWORD`） | 固定帳號，帳密一律由 `.env` 管理，不寫進文件 |
| 測試資料 | 依賴 dev 站台現有資料 | 需跨測試隔離時，每個 test 自行 cleanup（例：充值後提取歸零）|
| 環境 | 僅 dev 環境 | 禁止在 staging / prod 執行自動化 |
| `.env` | 開發者本機管理 | 禁止 commit；CI 用 Secrets |

---

## Marker 規範

### 必要 marker

所有測試 class 至少要有以下三類 marker：

1. **層級**：`p0` / `p1` / `p2`
2. **站點**：`rc` / `lt` / `re` / `rd` / `api`
3. **功能類別**：`login` / `home` / `wallet` / `i18n` / `visual` / `copy` 等

### Marker 新增條件

新增 marker 前需先：
1. 在 `pytest.ini` 宣告
2. 確認有至少 1 個測試會引用（避免空 marker）

### 實例

```python
@pytest.mark.p1
@pytest.mark.rc
@pytest.mark.i18n
@pytest.mark.language
class TestI18NHome:
    ...
```

---

## 執行指令速查

```bash
# 依站點
.venv/bin/pytest -m rc                    # RC 站全部
.venv/bin/pytest -m lt                    # LT 站全部
.venv/bin/pytest tests/api/               # API 全部

# 依層級
.venv/bin/pytest -m p0                    # 所有 smoke
.venv/bin/pytest -m p1                    # 所有 feature
.venv/bin/pytest -m "rc and p0"           # RC smoke

# 組合
.venv/bin/pytest -m "lt and i18n"         # LT i18n 套件
.venv/bin/pytest -m "rc and not i18n"     # RC 扣除 i18n

# 單檔
.venv/bin/pytest tests/rc/test_p0_smoke.py::TestLogin::test_login_success
```

---

## 現況盤點（2026-08-10）

涵蓋 **8 個前台站**（RC / LT / RE / RD / QW / LG / LU / RF）+ API + 後台 dashboard 層。
數量為 `pytest --collect-only` collected 數（**含 skip**，會隨 parametrize 展開）：

| 站點 | 前台 UI | API | 後台 | 小計 |
|------|--------|-----|------|------|
| RC   | 63     | 11  | 4    | 78   |
| LT   | 112    | 14  | 4    | 130  |
| RE   | 63     | 11  | 4    | 78   |
| RD   | 58     | 11  | 4    | 73   |
| QW   | 50     | 11  | 7    | 68   |
| LG   | 45     | 11  | 8    | 64   |
| LU   | 46     | 11  | 13   | 70   |
| RF   | 48     | 11  | 15   | 74   |
| **合計** | **485** | **91** | **59** | **635** |

> **KS 已於 2026-07 永久退役**（站點下架）。2026-08-05 將其 POM / 測試 / registry / marker / secrets 自 HEAD 全數移除，歷史程式碼見 git 歷史。退役前為 UI 43 / API 11 / 後台 6。

- **testcase 數量級拉平（2026-07-22 收官）**：後進 Nuxt 站（QW 48 / LG 44 / LU 43 / RF 48）已補齊至與 RC 系（58~63）同量級。
- **後台覆蓋**：信用版 RC / RE / LT / RD 為總代→代理 / 站長→會員 top_up；現金版 LU / LG / QW 站長主錢包 top_up（含 TOTP 2FA）+ 代理 read-only smoke；RF 信用版站長 + 代理 top_up。詳見 `docs/dashboard-technical-notes.md`。
- **API**：9 站結構齊備，各站 11 case（LT 14）。

執行時間（量級參考；實際以 CI artifact 為準）：

| 範圍 | 量級 |
|------|------|
| 單站 P0 smoke | 數分鐘 |
| 單站全套 UI（smoke + feature） | ~30 分鐘量級（站別而異） |
| API 全部 | < 1 分鐘 |
| 8 站全套 regression | 每週一經 `full-regression.yml` matrix 並行跑（見 `docs/cicd.md`） |

---

## 站點覆蓋邊界（Coverage boundary）

### QW 語系覆蓋邊界

QW（LM來財娛樂城）有 `LaiBetLanguage` cookie（`tw` / `en` / `cn` / `th` / `vn` 值合法），但 probe（2026-07-22 複驗）確認：

- **無語系切換 UI**（前台找不到任何切換入口）。
- **手動改 cookie 會被重置**、**頁面文案不隨 cookie 值變化**。

因此 QW 為**實質單語系顯示站**。i18n 覆蓋刻意停留在 **cookie 存在性 / 值格式層**（`tests/qw/feature/i18n` 現有 2 條），**不做 UI 文案多語系驗證** —— 產品無此能力，硬寫多語系文案斷言等於造假覆蓋。

**連帶影響**：QW feature 測試（如 member panel item、nav 分類）在無多語系切換 UI 的前提下，允許以**文字定位** panel item / 分類，並在測試 docstring 標註「文字定位風險已評估」。若未來 QW 開通語系切換 UI，需**重新 probe** 並將受影響測試改為結構化定位、i18n 覆蓋再向 UI 文案層擴充。

### 現金版前台存款覆蓋邊界（LU / LG / QW，2026-08-10 probe）

三站的存款入口行為**不一致**，測試因此分成兩條路徑：

| 站 | 存款入口 | 未綁銀行卡時 | 覆蓋做法 |
|----|---------|-------------|---------|
| LU | 頂部 nav 儲值 → in-page 錢包 dialog（URL 不變） | **無守衛**，直接進存款分頁 | 驗存款/提現分頁、付款平台格線非空且無空白格、送出鈕 enabled |
| LG | user menu 儲值 → `/member-center?type=Deposit` | 提示「請先綁定銀行卡」→ **約 1 秒後導向** `type=Withdrawal` | 驗最終落點提供「新增銀行卡」可操作入口 |
| QW | 首頁 shortcut-tile 存款 → 同上 | 同 LG | 同 LG |

兩條界線：

1. **一律不送出存款單**。送出會產生無法對稱回復的金流紀錄，違反 D-015；覆蓋停在「渠道/下一步呈現」。
2. **不為測試帳號綁定銀行卡**。綁卡是單向且汙染共用測試帳號的操作；改為把「未綁卡守衛」本身測起來 —— 它是真實業務規則，且守住「錯誤不渲染、留白頁無下一步」這類缺陷（產品 bug #11 前科）。

⚠️ LG/QW 的守衛測試**綁定當前測試資料狀態**（帳號 0 張銀行卡）。若日後帳號綁卡，存款頁不再被導走 → 該兩條會 fail，屆時應重新 probe 存款渠道 DOM 並改驗渠道呈現（LU-WALLET-006 為模板）。此 fail 是測試資料變更的訊號，不是誤報。

> 既有的 `test_wallet_link_navigates[Deposit]`（LG/QW）只驗 URL 瞬間帶 `type=Deposit`，在守衛導走前就斷言完畢 —— 綠燈**不代表**存款頁可用。新增的守衛測試補的正是這一層。

---

## 相關文件

- `CLAUDE.md` — 測試撰寫慣例、fixture 策略、POM 架構
- `docs/i18n_locale_text_reference.md` — 多語系文案對照
- `docs/dashboard-technical-notes.md` — 後台測試技術注意事項
- `dev-notes/regression-strategy.md` — 執行腳本與 CI/CD 規劃（尚未落地）
- `.claude/skills/ui-test-author/` — 新增測試的 checklist skill
