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
- Git commit 禁止包含 `Co-Authored-By: Claude` 行。

# Pre-commit workflow
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
6. 產出建議 commit message。

# Validation rules — 最小必要驗證
依變更範圍遞增：

| 變更範圍 | 建議驗證指令 |
|----------|-------------|
| 單一站點的單一測試檔 | `.venv/bin/pytest tests/<site_id>/<file>.py -v` |
| 單一站點的 page object | `.venv/bin/pytest tests/<site_id>/ -v` |
| 單一站點的 conftest | `.venv/bin/pytest tests/<site_id>/ -v` |
| factory.py | `.venv/bin/pytest tests/rc/ tests/lt/ -v`（所有已註冊站點） |
| 全域 conftest.py | `.venv/bin/pytest -v`（全量） |
| utils/*.py | `.venv/bin/pytest -v`（全量） |
| visual regression baseline | `.venv/bin/pytest -m visual_regression -v` |
| 新站點導入 | `.venv/bin/pytest tests/<new_site_id>/ -v` + 確認 factory 註冊 |

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
- 列出建議先執行的 pytest 指令。
- 指出是否適合直接 commit，或應先補驗證。
- 若有 diff red flags，逐條列出。
- 若有 multi-site 擴展性問題，先提醒。
- 提供 1~3 個 commit message 候選，遵循 `type(scope): description` 格式。
