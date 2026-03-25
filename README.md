# Auto Regression - Platform 自動化回歸測試

使用 **Python + pytest-playwright**，針對 Platform 遊戲站台進行端對端回歸測試，支援 Windows、WSL、Linux 三種環境自動偵測。

## 內容

- `tests/test_p0_smoke.py`：P0 冒煙測試，涵蓋登入、首頁、個人資訊、收件匣、遊戲廳、導覽列等核心流程（TC-001 ～ TC-022）
- `pages/login_page.py`：登入頁 Page Object，封裝導覽、開啟登入表單、送出帳密等操作
- `pages/home_page.py`：首頁 Page Object，封裝驗證登入狀態、導覽列點擊、登出等操作
- `utils/dialog_helper.py`：通用 UI 輔助，處理「伺服器錯誤」彈窗自動關閉、Loading 動畫等待
- `utils/screenshot_helper.py`：截圖系統，每個操作步驟自動高亮元素（紅框）並截圖，測試結束後產生繁體中文 README.md
- `config/settings.py`：多站台設定載入器，從 `.env` 讀取各站台的 URL / 帳號 / 密碼
- `conftest.py`：全域 pytest fixtures，處理環境偵測、瀏覽器啟動、自動登出、視窗最大化、截圖 attach/detach

## 安裝

```bash
cd ~/projects/auto-regression
cp .env.example .env        # 填入站台帳號密碼
pip install -r requirements.txt
playwright install chromium
```

## 執行

**請使用專案的 virtualenv（`.venv/`）執行所有指令。**

### 跑全部測試（使用 .env 預設站台）
```bash
.venv/bin/pytest
```

### 指定站台
```bash
.venv/bin/pytest --site=drc
```

### 只跑 P0
```bash
.venv/bin/pytest -m p0
```

### 只跑登入相關
```bash
.venv/bin/pytest -m login
```

### 只跑首頁相關
```bash
.venv/bin/pytest -m home
```

### 跑單一測試
```bash
.venv/bin/pytest tests/test_p0_smoke.py::TestLogin::test_login_success
```

### 查看 HTML 報表
```bash
# 測試完成後開啟
open reports/report.html
# WSL 下
explorer.exe reports/report.html
```

## WSL 測試流程

### 前置：確認 Port Proxy 轉發已設定（Windows PowerShell，系統管理員）

```powershell
# 查詢現有規則
netsh interface portproxy show all

# 若尚未設定 9223，新增轉發
netsh interface portproxy add v4tov4 listenaddress=<WINDOWS_HOST_IP> listenport=9223 connectaddress=127.0.0.1 connectport=9223
```

### 設定 .env

```
CDP_URL=http://<WINDOWS_HOST_IP>:9223
```

查詢 Windows host IP：
```bash
cat /etc/resolv.conf | grep nameserver
```

### 執行測試

```bash
cd ~/projects/auto-regression
pytest
```

`conftest.py` 偵測到 WSL 環境後，若 Chrome 尚未啟動，會自動呼叫 `chrome.exe` 並帶入以下參數：
- `--remote-debugging-port=9223`
- `--remote-debugging-address=0.0.0.0`
- `--user-data-dir=C:\temp\chrome-cdp-debug`

**不需要手動開 Chrome**，等待就緒後測試會自動開始。

---

## 環境說明

| 環境 | 瀏覽器啟動方式 |
|------|----------------|
| Windows | Playwright 直接啟動 Chrome |
| WSL | 自動啟動 Windows Chrome，透過 CDP 連接（port 9223） |
| Linux | 手動啟動 Chrome `--remote-debugging-port=9222`，設定 `CDP_URL` 後執行 |

Port 轉發與環境設定細節請參考 [PORTS_AND_SETUP.md](PORTS_AND_SETUP.md)。

## 說明

- 多站台支援：在 `.env` 增加 `SITE_XXX_URL / SITE_XXX_USERNAME / SITE_XXX_PASSWORD`，即可用 `--site=xxx` 切換
- 測試優先級以 marker 標記：`p0`（核心冒煙）、`p1`、`p2`（擴充回歸）
- `conftest.py` 內建 MutationObserver 注入，自動處理「伺服器錯誤」彈窗，避免測試中斷
- WSL 下若 Chrome 尚未開啟，`conftest.py` 會自動透過 `cmd.exe` 啟動並等待就緒
- 報表輸出至 `reports/report.html`，已加入 `.gitignore`
- 每個測試自動截圖並高亮操作元素（紅框），存於 `screenshots/<test_name>/`，並產生繁體中文操作流程 `README.md`；`screenshots/` 已加入 `.gitignore`
