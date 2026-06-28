# docs/

團隊共用的產品與技術文件資料夾。**內容會被 git 追蹤**，作為團隊共識的 source of truth。

---

## 用途定義

此資料夾存放「**需要跨開發者共享、且相對穩定**」的文件。任何新加入的團隊成員應該能透過閱讀本資料夾的內容，建立對測試套件與產品的理解。

### 應放入 `docs/` 的內容

- **產品事實參考**：例如多語系文案對照、API 契約、測試資料定義
- **測試策略與規格**：測試方向、覆蓋原則、case 設計規範
- **架構決策**：page object 設計、fixture 分層、站台擴充方式
- **慣例定義**：命名規則、selector 策略、截圖規範
- **Onboarding 指南**：新成員入門、環境建置、常見問題

### 不應放入 `docs/` 的內容

- 個人 TODO 或待辦清單 → 請放 [`dev-notes/`](../dev-notes/)
- 探索筆記、debug 紀錄、實驗結果 → 請放 `dev-notes/`
- 未成熟的改善提案、想法草稿 → 請放 `dev-notes/`
- Ephemeral 的工作進度 → 請放 `dev-notes/`

---

## 判斷原則（when in doubt）

寫新文件前先問自己：

1. **「半年後任何人看到這份文件都能理解並受用嗎？」**
   - 是 → `docs/`
   - 否 → `dev-notes/`
2. **「這是產品/測試的事實，還是我目前的想法？」**
   - 事實 → `docs/`
   - 想法 → `dev-notes/`
3. **「新進成員需要讀這份文件才能上手嗎？」**
   - 需要 → `docs/`
   - 不需要 → `dev-notes/`

---

## 現有文件

| 檔名 | 用途 |
|------|------|
| [`i18n_locale_text_reference.md`](./i18n_locale_text_reference.md) | 多語系文案對照表（LT 5 語系 + RC 6 語系 + RD 5 語系），`tests/**/feature/i18n/` 測試斷言的 source of truth |
| [`testing-strategy.md`](./testing-strategy.md) | 測試分層（L0~L3）、通過標準、flaky 處理、並行限制、marker 規範 |
| [`lt-dashboard-sitemap.md`](./lt-dashboard-sitemap.md) | LT 後台完整功能地圖（25 頁 × 8 分類），後台測試撰寫的事實參考 |
| [`dashboard-technical-notes.md`](./dashboard-technical-notes.md) | 後台測試技術注意事項（TOTP、browser context 分離、session 管理、fixture scope 策略） |
| [`cicd.md`](./cicd.md) | GitHub Actions 操作指南（trigger 規則 / cron / secrets / Slack 通知 + 聚合成績單 / 看 run / 下載 artifact / docs sync check） |
| [`agent-skills-workflow.md`](./agent-skills-workflow.md) | Agent / skill / subagent 6+3 接力工作流 |
| [`new-site-onboarding-workflow.md`](./new-site-onboarding-workflow.md) | 新站 onboarding 完整 SOP（mermaid 流程圖、subagent/skill 觸發條件、預估時間、QW 實作踩坑） |
| [`product-bugs-to-report.md`](./product-bugs-to-report.md) | 已確認的產品/前端/後端 bug 清單（待回報廠商），與「測試端待穩定」flaky 區分 |

---

## 維護原則

- 新增/修改文件時，同步更新本 README 的「現有文件」清單
- 文件內容與程式碼有關聯時（如 selector、case ID），需說明對應的檔案位置
- 文件過時請直接更新，不要保留「舊版」副本
- 若文件變成「個人筆記」，請移到 `dev-notes/`
