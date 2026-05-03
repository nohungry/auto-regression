# dev-notes/

個人開發過程的臨時參考筆記資料夾。**內容不進 git（僅本 README 被追蹤）**，每位開發者可自由在此放置自己的筆記。

---

## 用途定義

此資料夾存放「**個人的、經常變動的、不需團隊共識**」的工作筆記。文件僅代表撰寫者當下的觀察或想法，不是產品/測試的事實來源。

### 應放入 `dev-notes/` 的內容

- **個人 TODO / 待辦清單**：改善提案、待處理項目、想做但還沒做的事
- **探索筆記**：實機測試發現、selector 嘗試紀錄、行為觀察
- **Debug 紀錄**：問題排查過程、錯誤訊息、臨時解法
- **效能實驗**：benchmark 結果、優化嘗試
- **想法草稿**：架構構想、尚未成熟的改善方向
- **測試覆蓋比對**：與舊版本/其他專案的對照表
- **工具評估 / Spike**：新工具引入的探索與決策紀錄

### 不應放入 `dev-notes/` 的內容

- 團隊共用的事實文件 → 請放 [`docs/`](../docs/)
- 產品規格、API 契約、i18n 文案對照 → 請放 `docs/`
- 測試策略、架構決策、慣例定義 → 請放 `docs/`
- Onboarding 指南 → 請放 `docs/`

---

## 判斷原則（when in doubt）

寫新文件前先問自己：

1. **「半年後任何人看到這份文件都能理解並受用嗎？」** → 是 `docs/` / 否 `dev-notes/`
2. **「這是產品/測試的事實，還是我目前的想法？」** → 事實 `docs/` / 想法 `dev-notes/`
3. **「新進成員需要讀這份文件才能上手嗎？」** → 需要 `docs/` / 不需要 `dev-notes/`

升級路徑：若 dev-notes 中某份筆記已成熟並獲團隊共識，請**升級**移到 `docs/` 並調整內容為正式文件。

---

## 當前筆記索引（2026-05-03 整理）

> 索引按主題分組，每檔一句話描述用途。檔名後標註最後更新月份。

### 📋 待辦 / 規劃

| 檔案 | 用途 |
|------|------|
| [`pending-and-optimizations-2026-05-02.md`](pending-and-optimizations-2026-05-02.md) **(5月)** | **當前現役** — 2026-05-02 當下代辦快照（4 高優先 / 3 中優先 / 3 低優先 / 6 站 code 端代辦 / 4 程式碼小優化） |
| [`backlog.md`](backlog.md) (4月) | 歷史 backlog — A~K 任務歷程 + 結構化 P1/P2/P3 分類（4/14 後新增項見 pending-05-02） |
| [`regression-strategy.md`](regression-strategy.md) (4月) | 規劃完成、待實作 — 4 層 regression 策略 + scripts/regression.sh 範本 + CI/CD 4 階段（等 LT/RC 環境恢復後啟動 Phase 1） |

### 🎯 Dashboard 自動化

| 檔案 | 用途 |
|------|------|
| [`dashboard-handoff.md`](dashboard-handoff.md) (4月) | 後台自動化交接給同事的工作說明（SiteConfig 擴充、依賴、目錄 scaffold、.env 範本） |

> 5 個 dashboard tab probe（agent-revenue / agent-tab / snapshot-tabs / sub-account-tab / member-settings）已於 2026-05-03 整理時刪除 — 都是純 ARIA tree raw dump，過時且需重 probe 時用 `selector-probe` skill 1 秒重抓更快。

### 🌐 LT 站

| 檔案 | 用途 |
|------|------|
| [`lt-dashboard-sitemap.md`](lt-dashboard-sitemap.md) (4月) | LT 後台 sitemap（25 頁 × 8 分類）+ TOTP 登入技術細節（OTP input、native value setter） |

> `lt-site-redesign-2026-04.md`（LT input class rename 紀錄）已於 2026-05-03 整理時刪除 — 內容是 4/20 一次性 selector rename 紀錄，但 4/24 後 LT 又被新版整套改寫，紀錄已失效。

### 🔍 Code Review

| 檔案 | 用途 |
|------|------|
| [`luke-branch-review-fixes-2026-04.md`](luke-branch-review-fixes-2026-04.md) (4月) | Luke 分支 22 項 review issue 的修正細節（B/M 已 commit、Minor 待做、含 SW patch root cause 分析） |

### 🛠 工具評估 / Spike

| 檔案 | 用途 |
|------|------|
| [`agent-browser-spike-2026-05-02.md`](agent-browser-spike-2026-05-02.md) **(5月)** | agent-browser 工具評估報告 — spike 流程、結論「probe 工具不是 test runner」、數據附錄 |
| [`agent-browser-cookbook.md`](agent-browser-cookbook.md) **(5月)** | agent-browser 命令備忘 — setup（WSL ws://）、3 種場景、ARIA 判讀、5 條 pitfalls |

---

## Git 設定

此資料夾在 `.gitignore` 中設定為：
```
dev-notes/*
!dev-notes/README.md
```

只有本 README 會被追蹤，其他檔案都是本地檔案。

---

## 整理慣例

- **過時就刪**：dev-notes 是「丟棄式」筆記，內容過期（被新版取代、PR 已 merge、產品已改）就直接刪，不歸檔
- **加 header 標註現況**：保留價值的舊文件（如 `backlog.md` / `regression-strategy.md`），在開頭加標註指向最新狀態
- **每次大整理後更新本 README 的索引段**：保持當前筆記的可發現性
