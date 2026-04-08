# Port 配置與啟動說明

## Windows Port Proxy 轉發設定

WSL 無法直接用 `localhost` 連到 Windows，所以用 `netsh portproxy` 把流量從 WSL 虛擬網卡轉發到 Windows 本機。

> **注意：** `netstat` 查到 `<WINDOWS_HOST_IP>:<PORT>` 是 `svchost` 在監聽，這是正常現象——
> svchost 是 Windows Port Proxy 服務本身，負責接收並轉發流量，不是其他系統服務佔用。

### 查詢現有轉發規則
```powershell
netsh interface portproxy show all
```

### 新增轉發規則
```powershell
# 格式：將 WSL虛擬網卡IP:PORT 轉發到 Windows本機:PORT
netsh interface portproxy add v4tov4 listenaddress=<WINDOWS_HOST_IP> listenport=<PORT> connectaddress=127.0.0.1 connectport=<PORT>

# 範例：新增 9223 轉發（pytest 用）
netsh interface portproxy add v4tov4 listenaddress=<WINDOWS_HOST_IP> listenport=9223 connectaddress=127.0.0.1 connectport=9223

# 範例：新增 9224 轉發（MCP 用）
netsh interface portproxy add v4tov4 listenaddress=<WINDOWS_HOST_IP> listenport=9224 connectaddress=127.0.0.1 connectport=9224
```
> 需以**系統管理員身份**執行 PowerShell。

### 刪除轉發規則
```powershell
netsh interface portproxy delete v4tov4 listenaddress=<WINDOWS_HOST_IP> listenport=<PORT>
```

---

## Port 分工

| Port | 用途 |
|------|------|
| **9223** | pytest 自動化測試（WSL 模式） |
| **9224** | Claude Code + chrome-devtools MCP |

---

## 情境一：使用 Claude Code + MCP 進行 AI 輔助開發

### 目的
讓 Claude Code 透過 chrome-devtools MCP 觀察瀏覽器頁面，協助編寫測試。

### 啟動 Chrome（在 Windows PowerShell 執行）
```powershell
& "C:\Program Files\Google\Chrome\Application\chrome.exe" `
  --remote-debugging-port=9224 `
  --remote-debugging-address=0.0.0.0 `
  --user-data-dir="C:\temp\chrome-mcp"
```

**參數說明：**
- `--remote-debugging-port=9224`：開啟 CDP 遠端偵錯，使用 9224 port
- `--remote-debugging-address=0.0.0.0`：允許從 WSL（非 localhost）連入
- `--user-data-dir`：獨立的 Chrome 設定資料夾，避免影響日常使用的 Chrome

### 確認 Chrome 已在監聽（PowerShell）
```powershell
netstat -ano | findstr :9224
```
應看到 `127.0.0.1:9224` 或 `0.0.0.0:9224` 的 LISTENING。

### .mcp.json 設定

`.mcp.json` 包含機器專屬的 Windows host IP，已加入 `.gitignore`。請從範本建立：

```bash
cp .mcp.json.example .mcp.json
```

再將 `<WINDOWS_HOST_IP>` 替換為實際 IP（查詢方式：`cat /etc/resolv.conf | grep nameserver`）。

範本內容（`.mcp.json.example`）：
```json
{
  "mcpServers": {
    "chrome-devtools": {
      "type": "stdio",
      "command": "npx",
      "args": [
        "-y",
        "chrome-devtools-mcp@latest",
        "--slim",
        "--browser-url=http://<WINDOWS_HOST_IP>:9224"
      ],
      "env": {}
    },
    "playwright": {
      "type": "stdio",
      "command": "npx",
      "args": ["-y", "@playwright/mcp@latest", "--cdp-endpoint", "http://<WINDOWS_HOST_IP>:9224"],
      "env": {}
    }
  }
}
```

---

## 情境二：在 Windows PowerShell 跑 pytest

### 目的
直接在 Windows 執行自動化測試，Playwright 自動啟動 Chrome，不需要任何手動操作。

### 執行方式
```powershell
cd <PROJECT_PATH>
pytest
```

**不需要手動開 Chrome**，`conftest.py` 偵測到 Windows 環境後會由 Playwright 直接啟動。

### .env 相關設定
```
HEADLESS=false    # false = 顯示瀏覽器視窗，true = 背景執行
```
（Windows 模式下 `CDP_URL` 不會被使用）

---

## 情境三：在 WSL 跑 pytest

### 目的
從 WSL 開發環境執行自動化測試，自動透過 CDP 連線到 Windows Chrome。

### 執行方式
```bash
cd ~/projects/auto-regression
.venv/bin/pytest
```

**不需要手動開 Chrome**，`conftest.py` 偵測到 WSL 環境後，若 Chrome 尚未啟動，會自動呼叫 `chrome.exe` 並帶入以下參數：
- `--remote-debugging-port=9223`
- `--remote-debugging-address=0.0.0.0`
- `--user-data-dir=C:\temp\chrome-cdp-debug`

### .env 相關設定
```
CDP_URL=http://<WINDOWS_HOST_IP>:9223
```

**為什麼不用 `localhost`？**
WSL 無法用 `localhost` 連到 Windows，需要使用 Windows 主機在 WSL 虛擬網卡上的 IP（即 `<WINDOWS_HOST_IP>`）。

查詢 Windows host IP：
```bash
cat /etc/resolv.conf | grep nameserver
```

---

### 除錯：若 Chrome 啟動超時

若出現 `RuntimeError: Chrome 啟動超時` 請依序確認：

**Step 1：確認 port proxy 規則存在（PowerShell）**
```powershell
netsh interface portproxy show all
```
確認有 `<WINDOWS_HOST_IP>:9223 → 127.0.0.1:9223` 這條規則，沒有則新增：
```powershell
netsh interface portproxy add v4tov4 listenaddress=<WINDOWS_HOST_IP> listenport=9223 connectaddress=127.0.0.1 connectport=9223
```

**Step 2：手動啟動 Chrome（PowerShell）**
```powershell
& "C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9223 --remote-debugging-address=0.0.0.0 --user-data-dir="C:\temp\chrome-cdp-debug"
```

**Step 3：確認 Chrome 已在監聽（PowerShell）**
```powershell
netstat -ano | findstr :9223
```
應看到 `0.0.0.0:9223` 或 `127.0.0.1:9223` 的 LISTENING。

**Step 4：在 WSL 測試連線**
```bash
curl http://<WINDOWS_HOST_IP>:9223/json/version
```
有 JSON 回應即代表 port proxy 正常，再執行 `pytest`。

**Step 5：若 curl 仍然 timeout — 新增防火牆規則（PowerShell，系統管理員）**
```powershell
New-NetFirewallRule -DisplayName "WSL CDP 9223" -Direction Inbound -Protocol TCP -LocalPort 9223 -Action Allow
```
新增後重新執行 Step 4 確認連線，有回應即可執行 `pytest`。

---

## .env 完整範例

```
DEFAULT_SITE=drc
HEADLESS=false
CDP_URL=http://<WINDOWS_HOST_IP>:9223

SITE_DRC_URL=https://dev-drc.t9platform-ph.com/
SITE_DRC_USERNAME=your_username
SITE_DRC_PASSWORD=your_password

SITE_DLT_URL=https://dev-lt.t9platform.com/
SITE_DLT_USERNAME=your_username
SITE_DLT_PASSWORD=your_password
```

> 使用 `pytest tests/drc/` 或 `pytest tests/dlt/` 指定站點時，可忽略 `DEFAULT_SITE`（各站 conftest 會覆寫）。
