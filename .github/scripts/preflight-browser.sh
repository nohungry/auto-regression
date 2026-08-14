#!/usr/bin/env bash
# 瀏覽器管道 preflight：跑測試前先確認「瀏覽器接得上嗎」，接不上就**指名是哪一層**擋住。
#
# 為什麼需要：CDP 模式的路徑是 WSL → Windows 主機 → portproxy → Chrome，中間任一層斷掉，
# pytest 只會丟一句含糊的連線錯誤（甚至偽裝成「整批秒殺」）。2026-08-14 實例：Windows 更新
# 重開機後 CDP 全斷，逐層人工排查花了 20 分鐘，且中途因為只看了截斷的規則清單而誤判成
# 「缺 Hyper-V 防火牆規則」——實際規則早就存在，真兇在更底層。本腳本把那段排查固化下來，
# **有證據才下結論**：規則齊全卻仍被丟包時，不會硬指某層，而是報「靜默丟棄」並列出可疑的
# VPN / WFP 層，避免給出錯的修復指令。
#
# 用法：
#   .github/scripts/preflight-browser.sh          # 依環境自動判斷模式
#   BROWSER_MODE=local .github/scripts/preflight-browser.sh
#
# 離開碼：0 = 可以跑測試；1 = 管道不通（結論段會給下一步）

set -uo pipefail

if [ -t 1 ]; then
    GREEN=$'\033[0;32m'; RED=$'\033[0;31m'; YELLOW=$'\033[0;33m'; DIM=$'\033[2m'; NC=$'\033[0m'
else
    GREEN=''; RED=''; YELLOW=''; DIM=''; NC=''
fi
ok()   { echo "  ${GREEN}✅${NC} $*"; }
bad()  { echo "  ${RED}❌${NC} $*"; }
warn() { echo "  ${YELLOW}⚠️${NC}  $*"; }
info() { echo "  ${DIM}·${NC}  $*"; }
head_() { echo; echo "── $* ──"; }

PS='/mnt/c/Windows/System32/WindowsPowerShell/v1.0/powershell.exe'
NETSH='/mnt/c/Windows/System32/netsh.exe'

is_wsl() { [ -r /proc/version ] && grep -qi microsoft /proc/version; }
have_windows_tools() { is_wsl && [ -x "$PS" ]; }

# 切到 repo 根目錄（腳本可能被從任何 cwd 呼叫；要讀 .env 的 CDP_URL）
SCRIPT_DIR=$(cd "$(dirname "$0")" && pwd)
REPO_ROOT=$(git -C "$SCRIPT_DIR" rev-parse --show-toplevel 2>/dev/null)
[ -n "$REPO_ROOT" ] || REPO_ROOT=$(git rev-parse --show-toplevel 2>/dev/null)
[ -n "$REPO_ROOT" ] && cd "$REPO_ROOT"

# -----------------------------------------------------------------
# 1. 判定模式（與 conftest.py 的分支邏輯對齊）
# -----------------------------------------------------------------
head_ "執行模式"

lower() { printf '%s' "${1:-}" | tr 'A-Z' 'a-z'; }

if [ "$(lower "${CI:-}")" = "true" ]; then
    MODE=ci
elif [ "$(lower "${BROWSER_MODE:-}")" = "local" ]; then
    MODE=local
else
    MODE=cdp
fi

case "$MODE" in
    ci)    info "模式：CI（CI=true）→ Playwright 內建 chromium，預設 headless" ;;
    local) info "模式：local（BROWSER_MODE=local）→ Playwright 內建 chromium，預設有頭" ;;
    cdp)   info "模式：CDP → 連既有 Chrome（BROWSER_MODE / CI 皆未設）" ;;
esac
is_wsl && info "平台：WSL" || info "平台：$(uname -s)"

# -----------------------------------------------------------------
# 2a. launch 模式（CI / local）：不依賴 CDP，只需確認本機 chromium 與顯示環境
# -----------------------------------------------------------------
if [ "$MODE" != "cdp" ]; then
    head_ "本機 chromium"
    RC=0

    CHROME_BIN=$(ls -d "$HOME"/.cache/ms-playwright/chromium-*/chrome-linux*/chrome 2>/dev/null | head -1)
    if [ -n "$CHROME_BIN" ]; then
        ok "chromium 執行檔：$CHROME_BIN"
    else
        bad "找不到 Playwright 內建 chromium"
        info "修復：.venv/bin/playwright install chromium"
        RC=1
    fi

    if [ "$MODE" = "local" ] && [ "$(lower "${HEADLESS:-}")" != "true" ]; then
        if [ -n "${DISPLAY:-}" ] || [ -n "${WAYLAND_DISPLAY:-}" ]; then
            ok "顯示環境：DISPLAY=${DISPLAY:-未設} WAYLAND_DISPLAY=${WAYLAND_DISPLAY:-未設}"
        else
            warn "無 DISPLAY / WAYLAND_DISPLAY，有頭模式可能開不起來"
            info "改跑無頭：HEADLESS=true；或確認 WSLg 已啟用"
        fi
    fi

    echo
    if [ "$RC" = "0" ]; then
        echo "${GREEN}結論：可以跑測試${NC}（$MODE 模式，不依賴 CDP / Windows Chrome）"
    else
        echo "${RED}結論：本機 chromium 未就緒${NC}，見上方修復指令"
    fi
    exit "$RC"
fi

# -----------------------------------------------------------------
# 2b. CDP 模式：先試連，通了就結束；不通才逐層定位
# -----------------------------------------------------------------
head_ "CDP 連線"

CDP_URL_VAL="${CDP_URL:-}"
if [ -z "$CDP_URL_VAL" ] && [ -f .env ]; then
    CDP_URL_VAL=$(grep -E '^CDP_URL=' .env | head -1 | cut -d= -f2- | tr -d '\r"'"'"'')
fi
CDP_URL_VAL="${CDP_URL_VAL:-http://127.0.0.1:9222}"

CDP_HOST=$(printf '%s' "$CDP_URL_VAL" | sed -E 's#^https?://##; s#[:/].*$##')
CDP_PORT=$(printf '%s' "$CDP_URL_VAL" | sed -E 's#^https?://[^:]+:?##; s#/.*$##')
CDP_PORT="${CDP_PORT:-9222}"
info "CDP_URL：$CDP_URL_VAL（host=$CDP_HOST port=$CDP_PORT）"

if VER=$(curl -s --max-time 5 "$CDP_URL_VAL/json/version" 2>/dev/null) && [ -n "$VER" ]; then
    BROWSER_VER=$(printf '%s' "$VER" | sed -nE 's/.*"Browser": *"([^"]+)".*/\1/p')
    ok "CDP 可連線：${BROWSER_VER:-（版本未知）}"
    echo
    echo "${GREEN}結論：可以跑測試${NC}（CDP 模式）"
    exit 0
fi

bad "CDP 連不上（curl 逾時或無回應）—— 以下逐層定位"

if ! have_windows_tools; then
    echo
    info "非 WSL 或找不到 Windows 工具，無法往下逐層檢查"
    echo "${RED}結論：CDP 不可用${NC} —— 確認 Chrome 已帶 --remote-debugging-port=$CDP_PORT 啟動，"
    echo "      或改用備援管道：BROWSER_MODE=local .venv/bin/pytest ..."
    exit 1
fi

MISSING=""          # 缺件（可直接指名修復）
add_missing() { MISSING="${MISSING}${MISSING:+, }$1"; }

# L1 — Windows 端 Chrome process
head_ "L1 Windows Chrome process"
CL=$("$PS" -NoProfile -Command "Get-CimInstance Win32_Process -Filter \"Name='chrome.exe'\" | Where-Object { \$_.CommandLine -like '*remote-debugging-port=$CDP_PORT*' } | Select-Object -First 1 -ExpandProperty CommandLine" 2>/dev/null | tr -d '\r')
if [ -n "$CL" ]; then
    ok "有帶 --remote-debugging-port=$CDP_PORT 的 Chrome 在跑"
    case "$CL" in
        *remote-debugging-address=0.0.0.0*) info "旗標含 --remote-debugging-address=0.0.0.0" ;;
        *) warn "未帶 --remote-debugging-address=0.0.0.0（需靠 portproxy 轉發）" ;;
    esac
else
    bad "找不到帶 --remote-debugging-port=$CDP_PORT 的 Chrome"
    info "修復：conftest 在 WSL 下會自動啟動；或手動 —— chrome.exe --remote-debugging-port=$CDP_PORT --remote-debugging-address=0.0.0.0 --user-data-dir=C:\\temp\\chrome-cdp-debug"
    add_missing "L1 Chrome 未啟動"
fi

# L2 — Windows 端監聽
head_ "L2 Windows 端監聽狀態"
LISTEN=$("$PS" -NoProfile -Command "(Get-NetTCPConnection -State Listen -LocalPort $CDP_PORT -ErrorAction SilentlyContinue | Select-Object -ExpandProperty LocalAddress) -join ','" 2>/dev/null | tr -d '\r')
NEED_PROXY=1
if [ -n "$LISTEN" ]; then
    ok "port $CDP_PORT LISTENING（綁定位址：$LISTEN）"
    case "$LISTEN" in
        *0.0.0.0*) info "已綁 0.0.0.0，理論上不需 portproxy"; NEED_PROXY=0 ;;
        *)         info "只綁 loopback，需靠 portproxy 從 $CDP_HOST 轉進來" ;;
    esac
else
    bad "Windows 端沒有任何 process 監聽 port $CDP_PORT"
    add_missing "L2 無人監聽"
fi

# L3 — portproxy
head_ "L3 netsh portproxy 轉發"
PP=$("$NETSH" interface portproxy show v4tov4 2>/dev/null | tr -d '\r' | grep -E "[[:space:]]$CDP_PORT[[:space:]]")
if [ -n "$PP" ]; then
    ok "有轉發規則：$(printf '%s' "$PP" | tr -s ' ')"
elif [ "$NEED_PROXY" = "0" ]; then
    info "Chrome 已綁 0.0.0.0，無 portproxy 亦可"
else
    bad "查無 port $CDP_PORT 的 portproxy 轉發"
    info "修復：netsh interface portproxy add v4tov4 listenaddress=$CDP_HOST listenport=$CDP_PORT connectaddress=127.0.0.1 connectport=$CDP_PORT"
    add_missing "L3 無 portproxy"
fi

# L4 — 傳統防火牆（netsh advfirewall）
head_ "L4 傳統防火牆規則"
FW=$("$PS" -NoProfile -Command "Get-NetFirewallRule -Direction Inbound -Action Allow -Enabled True -ErrorAction SilentlyContinue | Get-NetFirewallPortFilter -ErrorAction SilentlyContinue | Where-Object { \$_.LocalPort -eq '$CDP_PORT' } | Select-Object -First 1 -ExpandProperty LocalPort" 2>/dev/null | tr -d '\r')
if [ -n "$FW" ]; then
    ok "有放行 port $CDP_PORT 的 inbound 規則"
else
    bad "查無放行 port $CDP_PORT 的傳統防火牆規則"
    info "修復（系統管理員）：New-NetFirewallRule -DisplayName \"WSL CDP $CDP_PORT\" -Direction Inbound -Protocol TCP -LocalPort $CDP_PORT -Action Allow"
    add_missing "L4 傳統防火牆未放行"
fi

# L5 — Hyper-V 防火牆（WSL 專屬層，與 L4 是兩套獨立系統）
head_ "L5 Hyper-V 防火牆（WSL 專屬層）"
VMID=$("$PS" -NoProfile -Command "Get-NetFirewallHyperVVMSetting -PolicyStore ActiveStore -ErrorAction SilentlyContinue | Select-Object -First 1 -ExpandProperty Name" 2>/dev/null | tr -d '\r')
INBOUND=$("$PS" -NoProfile -Command "Get-NetFirewallHyperVVMSetting -PolicyStore ActiveStore -ErrorAction SilentlyContinue | Select-Object -First 1 -ExpandProperty DefaultInboundAction" 2>/dev/null | tr -d '\r')

if [ -z "$VMID" ]; then
    info "本機無 Hyper-V 防火牆設定（Windows 版本較舊或未啟用），略過"
else
    info "VMCreatorId：$VMID（DefaultInboundAction=${INBOUND:-未知}）"
    HVRULE=$("$PS" -NoProfile -Command "Get-NetFirewallHyperVRule -PolicyStore ActiveStore -ErrorAction SilentlyContinue | Where-Object { \$_.Direction -eq 'Inbound' -and \$_.Action -eq 'Allow' -and \$_.Enabled -eq 'True' -and \$_.LocalPorts -eq '$CDP_PORT' } | Select-Object -First 1 -ExpandProperty DisplayName" 2>/dev/null | tr -d '\r')
    if [ -n "$HVRULE" ]; then
        ok "已有 Hyper-V 放行規則：$HVRULE"
    elif [ "$INBOUND" = "Allow" ]; then
        ok "DefaultInboundAction = Allow（不需個別規則）"
    else
        bad "DefaultInboundAction = ${INBOUND:-未知}，且查無 port $CDP_PORT 的 Hyper-V 放行規則"
        info "這層與 L4 是兩套獨立系統 —— L4 規則再多也管不到它"
        info "修復（系統管理員）：New-NetFirewallHyperVRule -Name \"WSL-CDP-$CDP_PORT\" -DisplayName \"WSL CDP $CDP_PORT\" -Direction Inbound -VMCreatorId '$VMID' -Protocol TCP -LocalPorts $CDP_PORT -Action Allow"
        add_missing "L5 Hyper-V 防火牆未放行"
    fi
fi

# L6 — 封包是否被靜默丟棄（規則都齊卻不通時的關鍵證據）
head_ "L6 封包丟棄偵測"
DROPPED=0
if ip neigh show "$CDP_HOST" 2>/dev/null | grep -qE 'REACHABLE|STALE|DELAY'; then
    ok "ARP 可解析主機 $CDP_HOST（L2 正常，主機確實在線）"
    # 對 CDP port 做 TCP 連線：逾時＝封包被丟棄；connection refused＝路徑通、只是沒服務
    timeout 4 bash -c "exec 3<>/dev/tcp/$CDP_HOST/$CDP_PORT" 2>/dev/null
    case $? in
        124) bad "TCP 連線逾時（封包被**靜默丟棄**，不是 connection refused）"; DROPPED=1 ;;
        0)   ok "TCP 可建立連線（HTTP 層問題，非網路層）" ;;
        *)   info "connection refused —— 路徑通、該 port 沒服務（回頭看 L1/L2）" ;;
    esac
else
    warn "ARP 查不到 $CDP_HOST，WSL 網路可能異常"
fi

VPN_UP=$("$PS" -NoProfile -Command "(Get-NetAdapter | Where-Object { \$_.Status -eq 'Up' -and (\$_.Name -match 'nord|vpn|radmin|wireguard|tap' -or \$_.InterfaceDescription -match 'nord|vpn|radmin|wireguard|tap') } | Select-Object -ExpandProperty Name) -join ', '" 2>/dev/null | tr -d '\r')
if [ -n "$VPN_UP" ]; then
    warn "偵測到啟用中的 VPN / 虛擬網卡：$VPN_UP"
    [ "$DROPPED" = "1" ] && info "VPN 的 kill switch / LAN 阻擋會在 WFP 層丟包，比防火牆規則更底層 —— 規則再對也沒用"
else
    info "無啟用中的 VPN 介面"
fi

# -----------------------------------------------------------------
# 3. 結論：有缺件就指名缺件；全齊卻被丟包則報「更底層阻擋」，不硬指某層
# -----------------------------------------------------------------
echo
if [ -n "$MISSING" ]; then
    echo "${RED}結論：CDP 不可用${NC} —— 缺件：$MISSING（見上方對應修復指令）"
elif [ "$DROPPED" = "1" ]; then
    echo "${RED}結論：管道各層設定齊全，但封包在主機被靜默丟棄${NC}"
    echo "      → 阻擋發生在防火牆規則之下的層級（WFP filter），最常見是 VPN 用戶端"
    [ -n "$VPN_UP" ] && echo "      → 目前啟用中：$VPN_UP"
    echo
    echo "  決定性測試（30 秒）："
    echo "    1. 暫時中斷 VPN 連線（或關閉其 kill switch / 區網阻擋）"
    echo "    2. curl -s --max-time 5 $CDP_URL_VAL/json/version"
    echo "    有 JSON 回應 → 兇手確定；之後在 VPN 設定開啟「允許區域網路存取」即可長期共存"
else
    echo "${RED}結論：CDP 不可用${NC}，但逐層檢查未發現缺件 —— 見上方各層結果人工判讀"
fi
echo
echo "${YELLOW}不想等修復？${NC}改用備援管道，完全不碰 CDP（D-025）："
echo "  BROWSER_MODE=local .venv/bin/pytest tests/rc/test_p0_smoke.py"
exit 1
