# 測試策略與執行規範

> 最後更新：2026-04-14
> 適用範圍：`tests/` 全部（RC、LT、API、Dashboard）

本文件定義測試套件的分層、通過標準、與執行規範。實作腳本與 CI/CD 細節另見 `dev-notes/regression-strategy.md`（目前為規劃階段）。

---

## 測試分層（Level）

| 層級 | 範圍 | 目標耗時 | 目的 |
|------|------|---------|------|
| **L0 Sanity** | API 健康度 + 單站 smoke 核心 3 項 | < 2 分鐘 | 快速驗證環境與後端活著 |
| **L1 Smoke** | 兩站 P0 smoke 全跑（26 tests） | ~10 分鐘 | 核心流程健康度 |
| **L2 Feature** | 兩站 P1 feature 全跑（~139 tests） | ~45 分鐘 | 功能層回歸 |
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
| **RC 與 LT 可並行** | 不同帳號、不同站台，彼此不衝突 |
| **API 可獨立並行** | 不依賴瀏覽器，但仍受同帳號規則限制 |

---

## 測試資料管理

| 類型 | 現況 | 規範 |
|------|------|------|
| 測試帳號 | RC: `norman001` / LT: `dlttest01` | 固定帳號，密碼在 `.env` 管理 |
| 測試資料 | 依賴 dev 站台現有資料 | 需跨測試隔離時，每個 test 自行 cleanup（例：充值後提取歸零）|
| 環境 | 僅 dev 環境 | 禁止在 staging / prod 執行自動化 |
| `.env` | 開發者本機管理 | 禁止 commit；CI 用 Secrets |

---

## Marker 規範

### 必要 marker

所有測試 class 至少要有以下三類 marker：

1. **層級**：`p0` / `p1` / `p2`
2. **站點**：`rc` / `lt` / `api`
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

## 現況盤點（2026-04-14）

| 站點 | Smoke (P0) | Feature (P1) | API | 合計 |
|------|-----------|--------------|-----|------|
| RC   | 8         | 49 (含 skip) | 2   | 59   |
| LT   | 18        | 90           | 14  | 122  |
| **合計** | **26** | **139** | **16** | **181** |

執行時間（WSL + Chrome CDP 實測）：

| 範圍 | 耗時 |
|------|------|
| RC 全站 UI | ~32 分鐘 |
| LT 全站 UI | ~32 分鐘（smoke + feature）|
| API 全部 | < 1 分鐘 |
| 全套 UI + API | ~56 分鐘 |

---

## 相關文件

- `CLAUDE.md` — 測試撰寫慣例、fixture 策略、POM 架構
- `docs/i18n_locale_text_reference.md` — 多語系文案對照
- `docs/dashboard-technical-notes.md` — 後台測試技術注意事項
- `dev-notes/regression-strategy.md` — 執行腳本與 CI/CD 規劃（尚未落地）
- `.claude/skills/ui-test-author/` — 新增測試的 checklist skill
