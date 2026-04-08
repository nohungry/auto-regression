# Auto Regression - Platform 自動化回歸測試

使用 **Python + pytest-playwright**，針對 T9 Platform 遊戲站台進行端對端回歸測試，支援 Windows、WSL、Linux 三種環境自動偵測。

## 支援站台

| 站台 ID | 網址 | 測試數 |
|---------|------|--------|
| `drc` | dev-drc.t9platform-ph.com | 51 |
| `dlt` | dev-lt.t9platform.com | 93（含 30 tests SKIP 中）|
| API | - | 2 |

> 測試數以 `.venv/bin/pytest --collect-only -q` 為準，會隨新增測試變動。

## 目錄結構

```
conftest.py                          — 全域 fixtures、環境偵測、MutationObserver 注入（drc 專用）
config/settings.py                   — 多站台 SiteConfig，從 .env 讀取
pages/factory.py                     — site_id → LoginPage/HomePage 路由（registry dict）
pages/drc/                           — drc 站 Page Objects
pages/dlt/                           — dlt 站 Page Objects
tests/api/dlt/                       — dlt 站 API 層測試（不啟動瀏覽器）
tests/drc/                           — drc 站測試
  ├── conftest.py                    — drc 專屬：site_config 覆寫、go_home 含公告彈窗處理
  ├── test_p0_smoke.py               — p0 核心流程
  ├── test_language.py               — 多語系下拉結構驗證（暫留）
  └── feature/
      ├── announcement_popup/        — 首頁公告彈窗測試
      ├── i18n/                      — 多語系文案（home/login/sidebar，6 語系）
      ├── navigation/                — 分類導覽
      └── wallet/                    — 餘額相關
tests/dlt/                           — dlt 站測試
  ├── conftest.py                    — dlt 專屬：site_config 覆寫、page fixture 不注入 MutationObserver
  ├── test_p0_smoke.py               — p0 核心流程
  ├── test_locale_visual_matrix.py   — 多語系截圖矩陣（全 SKIP，待定）
  ├── __snapshots__/                 — Visual Regression baseline（目前暫時廢棄）
  └── feature/
      ├── auth/                      — 登入後功能
      ├── copy/                      — 文案一致性（預設繁中）
      ├── i18n/                      — 多語系文案（home/login/drawer，5 語系）
      ├── member/                    — 會員功能（個人資料/收件匣/投注紀錄）
      ├── public/                    — 公開頁延伸（客服/版權/語系 icon）
      ├── visual/                    — DOM 視覺健康度 + VR reference 截圖
      └── wallet/                    — 餘額/存款入口
utils/locale_helper.py               — set_locale()：注入 i18n_redirected_lt cookie
utils/dialog_helper.py               — 伺服器錯誤彈窗、公告彈窗、Loading 等待
utils/screenshot_helper.py           — 截圖系統（元素高亮 + 自動產生繁中 README）
docs/                                — 團隊共用文件（追蹤於 git）
dev-notes/                           — 個人開發筆記（gitignored，僅 README 追蹤）
screenshots/                         — 每個測試的截圖與報告（gitignored）
reports/report.html                  — pytest-html 測試報表
```

> 詳細分工與判斷原則請參考 [`docs/README.md`](docs/README.md) 與 [`dev-notes/README.md`](dev-notes/README.md)。

## 安裝

```bash
cp .env.example .env        # 填入站台帳號密碼與 CDP_URL
pip install -r requirements.txt
playwright install chromium
```

## 執行

**請使用專案 virtualenv（`.venv/`）執行所有指令。**

```bash
.venv/bin/pytest                                                          # 全部測試
.venv/bin/pytest tests/drc/                                               # drc 站
.venv/bin/pytest tests/dlt/                                               # dlt 站
.venv/bin/pytest tests/api/                                               # 僅 API 測試
.venv/bin/pytest tests/dlt/test_p0_smoke.py -m p0                         # dlt P0 smoke
.venv/bin/pytest -m p0                                                    # 所有站台 P0
.venv/bin/pytest -m "dlt and i18n"                                        # dlt 多語系測試
.venv/bin/pytest tests/drc/test_p0_smoke.py::TestLogin::test_login_success # 單一測試
```

### Visual Regression

DLT 站目前採用 **reference screenshot** 策略（存檔供人工確認，不做 pixel 比對）：

```bash
# 執行 VR reference 截圖測試（輸出至 screenshots/dlt/vr_reference/）
.venv/bin/pytest tests/dlt/feature/visual/test_visual_regression.py -m visual_regression

# DOM 層視覺健康度（非截圖）
.venv/bin/pytest tests/dlt/feature/visual/test_visual.py -m visual
```

> `tests/dlt/test_locale_visual_matrix.py`（WIN-LVIS）目前全部 `skip`，因 pixel-level 比對無法跨環境穩定運作。  
> `tests/dlt/__snapshots__/` 為舊版 baseline 暫留，目前無測試引用。

### 查看 HTML 報表

```bash
explorer.exe reports/report.html   # WSL
```

## WSL 設定

### 1. 設定 Port Proxy（Windows PowerShell，系統管理員）

```powershell
netsh interface portproxy add v4tov4 listenaddress=<WINDOWS_IP> listenport=9223 connectaddress=127.0.0.1 connectport=9223
```

### 2. 設定 .env

```
CDP_URL=http://<WINDOWS_IP>:9223
```

查詢 Windows IP：
```bash
cat /etc/resolv.conf | grep nameserver
```

### 3. 執行測試

`conftest.py` 偵測到 WSL 後，若 Chrome 尚未啟動會自動呼叫 `chrome.exe --remote-debugging-port=9223`，不需手動開啟瀏覽器。

## 環境對照

| 環境 | 瀏覽器啟動方式 |
|------|----------------|
| Windows | Playwright 直接啟動 |
| WSL | 自動啟動 Windows Chrome，透過 CDP 連接（port 9223） |
| Linux | 手動啟動 Chrome `--remote-debugging-port=9222`，設定 `CDP_URL` |

Port 轉發與環境設定細節請參考 [PORTS_AND_SETUP.md](PORTS_AND_SETUP.md)。

## 測試分級與 Markers

### 優先級

| Marker | 說明 |
|--------|------|
| `p0` | 核心 Smoke，每次 Release 必跑 |
| `p1` | 功能驗證，重大版本必跑 |
| `p2` | 視覺/完整回歸 |

### 功能分類

| Marker | 說明 |
|--------|------|
| `login` | 登入相關 |
| `home` | 首頁相關 |
| `member` | 會員功能（個人資料/收件匣） |
| `wallet` | 餘額/存款相關 |
| `i18n` | 多語系文案驗證 |
| `language` | 多語系切換行為 |
| `copy` | 文案一致性（預設語系） |
| `visual` | DOM 層視覺健康度（非截圖） |
| `visual_regression` | 截圖 baseline / reference |
| `locale_visual` | 多語系截圖矩陣 |
| `api` | API 層測試（不啟動瀏覽器） |

### 站台

| Marker | 說明 |
|--------|------|
| `dlt` | dlt 站點（DLT 來財）專屬測試 |

> 完整 markers 定義請見 [`pytest.ini`](pytest.ini)。

## 文件資源

| 路徑 | 用途 |
|------|------|
| [`docs/`](docs/) | 團隊共用的事實/策略/規格文件（追蹤於 git） |
| [`docs/i18n_locale_text_reference.md`](docs/i18n_locale_text_reference.md) | 多語系文案對照表（DLT + DRC） |
| [`CLAUDE.md`](CLAUDE.md) | Claude Code 協作指南與慣例定義 |
| [`PORTS_AND_SETUP.md`](PORTS_AND_SETUP.md) | Port 轉發與環境設定 |
| [`dev-notes/`](dev-notes/) | 個人開發筆記（gitignored，僅 README 追蹤） |

## 說明

- **多站台支援**：在 `.env` 增加 `SITE_XXX_URL / SITE_XXX_USERNAME / SITE_XXX_PASSWORD`，於 `pages/<site_id>/` 建立 page objects，在 `pages/factory.py` 的 registry dict 註冊，再於 `tests/<site_id>/` 建立測試目錄即可
- **伺服器錯誤彈窗**：`conftest.py` 內建 MutationObserver 注入，自動處理 drc 站的伺服器錯誤彈窗；dlt 站在 `tests/dlt/conftest.py` 覆寫 `page` fixture 關閉此注入
- **截圖系統**：每個測試自動截圖並高亮操作元素（紅框），存於 `screenshots/<site_id>/<timestamp>/<test_name>/`，並產生繁中操作流程 README
- **報表與截圖**：`reports/`、`screenshots/` 均已加入 `.gitignore`
