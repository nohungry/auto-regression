# Port 配置與啟動說明

## Windows Port Proxy 轉發設定

WSL 無法直接用 `localhost` 連到 Windows，所以用 `netsh portproxy` 把流量從 WSL 虛擬網卡轉發到 Windows 本機。

### 目前已設定的轉發規則
```
172.29.96.1:9222  →  127.0.0.1:9222
```
WSL 連到 `172.29.96.1:9222`，Windows 自動轉發到 `127.0.0.1:9222`（本機 Chrome）。

> **注意：** `netstat` 查到 `172.29.96.1:9222` 是 `svchost` 在監聽，這是正常現象——
> svchost 是 Windows Port Proxy 服務本身，負責接收並轉發流量，不是其他系統服務佔用。

### 查詢現有轉發規則
```powershell
netsh interface portproxy show all
```

### 新增轉發規則
```powershell
# 格式：將 WSL虛擬網卡IP:PORT 轉發到 Windows本機:PORT
netsh interface portproxy add v4tov4 listenaddress=172.29.96.1 listenport=<PORT> connectaddress=127.0.0.1 connectport=<PORT>

# 範例：新增 9223 轉發（pytest 用）
netsh interface portproxy add v4tov4 listenaddress=172.29.96.1 listenport=9223 connectaddress=127.0.0.1 connectport=9223

# 範例：新增 9224 轉發（MCP 用）
netsh interface portproxy add v4tov4 listenaddress=172.29.96.1 listenport=9224 connectaddress=127.0.0.1 connectport=9224
```
> 需以**系統管理員身份**執行 PowerShell。

### 刪除轉發規則
```powershell
netsh interface portproxy delete v4tov4 listenaddress=172.29.96.1 listenport=<PORT>
```

---

## Port 分工

| Port | 用途 | 原因 |
|------|------|------|
| **9222** | MCP chrome-devtools（舊設定） | 已有 portproxy 轉發 172.29.96.1:9222 → 127.0.0.1:9222 |
| **9223** | pytest 自動化測試（WSL 模式） | 需另外新增 portproxy 轉發規則 |
| **9224** | Claude Code + chrome-devtools MCP（新設定） | 需另外新增 portproxy 轉發規則 |

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
        "--browser-url=http://172.29.96.1:9224"
      ]
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
cd C:\TT99_wolaowla
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
cd /mnt/c/TT99_wolaowla
pytest
```

**不需要手動開 Chrome**，`conftest.py` 偵測到 WSL 環境後，若 Chrome 尚未啟動，會自動呼叫 `chrome.exe` 並帶入以下參數：
- `--remote-debugging-port=9223`
- `--remote-debugging-address=0.0.0.0`
- `--user-data-dir=C:\temp\chrome-cdp-debug`

### .env 相關設定
```
CDP_URL=http://172.29.96.1:9223
```

**為什麼用 `172.29.96.1`？**
WSL 無法用 `localhost` 連到 Windows，需要使用 Windows 主機在 WSL 虛擬網卡上的 IP。

查詢 Windows host IP：
```bash
cat /etc/resolv.conf | grep nameserver
```

---

## .env 完整範例

```
DEFAULT_SITE=wlj
HEADLESS=false
CDP_URL=http://172.29.96.1:9223

SITE_WLJ_URL=https://dev-drc.t9platform-ph.com/
SITE_WLJ_USERNAME=your_username
SITE_WLJ_PASSWORD=your_password
```
