# 後台 Dashboard 測試技術注意事項

> 最後更新：2026-07-24
> 適用範圍：所有後台（dashboard）自動化測試

本文件整理後台測試撰寫時容易踩坑的技術規則。功能地圖請見 `docs/lt-dashboard-sitemap.md`。

---

## TOTP 2FA 登入流程

> **實作現況（2026-06-23 更新）**：信用版 `/management` 後台（RC，LT/RE re-export RC）
> 目前帳密實際無 2FA，但 `DashboardLoginPage` 已內建**條件式 2FA**：`login()` 收選用
> `totp_secret`，僅當有 secret 時才偵測 modal 並填碼，無 secret 則零延遲跳過
> → 未來任一信用版站長/代理啟用 2FA，只要 `.env` 填對應 TOTP 即自動生效，不需改 code。
> **設計原則：所有站長預設都應有 2FA**，登入處理一律條件式支援（RE 站長目前為無 2FA 的暫時例外）。
> **LU（Dlu測試站）是第一個真正把 TOTP 2FA 寫進登入流程的站**（Vue admin 結構），
> 共用碼集中在 `utils/totp_helper.py`（pyotp 產碼）。
> ⚠️ 信用版 2FA modal 填碼路徑尚未實機驗證（目前無啟用 2FA 的信用版帳號），
> selector 暫沿用 LU Vue admin（`.dialog-container`/`input.otp-box`），待實際啟用時 probe 校正。

### 規則 1：OTP input 結構因站而異，先 probe 再決定填法

TOTP modal 的 OTP input 並非各站相同，**寫 code 前必先實機 probe**，再選填法：

| Pattern | 站台 | OTP 結構 | 填法 |
|---------|------|---------|------|
| **A — 多格獨立 box** | **LU**（已實作） | 6 個 `input.otp-box`（`maxlength=1`），彈窗 `.dialog-container`「Two-Factor Authentication」，送出 `button.confirm-btn`「Confirm」 | 逐格 `locator.nth(i).fill(code[i])`；Vue 元件自動推進焦點。每格重新 query locator 避免 re-render detached |
| **B — 單一 hidden input** | LT 舊探勘記錄（**尚未實作於 code**） | 自訂 React component `input.otp-hidden-input`，一般 `fill()`/`type()` 不觸發 state 更新 | native value setter + `dispatchEvent('input')`（見下方） |

#### Pattern A（LU 實際做法）

```python
from utils.totp_helper import get_totp_code

code = get_totp_code(site_config.dashboard_totp)  # 含過期緩衝
boxes = page.locator("input.otp-box")
for i, digit in enumerate(code):
    boxes.nth(i).fill(digit)
page.locator("button.confirm-btn", has_text="Confirm").click()
```

#### Pattern B（若遇到單一 hidden input 自訂 component）

```python
page.evaluate("""(code) => {
    const input = document.querySelector('input.otp-hidden-input');
    const setter = Object.getOwnPropertyDescriptor(
        window.HTMLInputElement.prototype, 'value').set;
    setter.call(input, code);
    input.dispatchEvent(new Event('input', { bubbles: true }));
}""", code)
```

### 規則 2：TOTP 30 秒輪轉必須預留緩衝

TOTP 每 30 秒輪轉一次，若 code 在提交瞬間過期會驗證失敗。**統一用 `utils/totp_helper.get_totp_code()`**
（modal 出現後才產碼，剩餘秒數不足會自動等下一窗口）：

```python
from utils.totp_helper import get_totp_code
code = get_totp_code(site_config.dashboard_totp, min_remaining=5)
```

### 規則 2b：避免短時間多次 2FA 登入（rate-limit / lockout）

實戰教訓（2026-06-12）：短時間內對同一後台帳號反覆登入（probe 多輪 + session fixture
登入失敗被每個 test 重試 + `--reruns`）會觸發後端 **2FA 鎖定 / 登入頻率限制**，之後每次
TOTP 都被拒（OTP 元件填滿自動送出 → 清空 → 停在 `#/login`）。對策：
- session-scoped `dashboard_page` 全套只登入一次；probe 期間節制登入次數。
- 連續兩次登入間隔 > 30s（避免同 TOTP 窗口重放被拒）。
- 疑似鎖定時**停手等冷卻 ~20-30 分鐘**再跑，不要繼續重試（會延長鎖定）。

---

## LU（Dlu測試站）後台導航 / logout selector

實機 probe（2026-06-12，站長 <LU 站長帳號>）。LU 後台 Vue hash SPA，與 RC/RE 不同框架：

- **側欄 `.sidebar.hide`（收合/移出畫面）** → 所有側欄連結在 viewport 外，**必須
  `dispatch_event("click")`**（仿 RC CSS-hidden sidebar，見本檔「元素互動例外」精神）。
- 頂層選單 `.sidebar-nav li.parent-li`（站長 18 項）；父項錨點 `a.memberSpan` 帶
  `id`=route（如 `id="/member"`），**locale-agnostic 穩定 selector**。
- 葉節點 `a[href^='#/...']`（如 `#/member/member-registration`）即使側欄收合仍在 DOM，
  可直接 dispatch 導航。導航判定：URL hash 變化 + `.app-main-content` 可見（不綁文案，
  後台 locale 混雜英文 + 未翻譯 i18n key）。
- **logout**：點右上 `.user-account`（顯示帳號）開下拉選單 → `Reset Password / Wallet /
  Agent Information / Logout` → 點 `Logout`（`get_by_role("link", name="Logout")`）→ 回 `#/login`。
- ⚠️ **帳號層級**：目前以站長帳號驗證（可見 18 項選單）；下級代理帳號權限/選單不同，
  需另立代理層級測試 —— 入口 URL 與帳號欄位差異見下節「後台站台覆蓋現況 + 代理 vs 站長入口」。

---

## 後台站台覆蓋現況 + 代理 vs 站長入口

### top_up 大線全面完整（2026-06-27 更新，9 站皆有後台測試）

> 本節為後台覆蓋的**最新事實**；其下 2026-06-24 的「已覆蓋後台站台」表與「後台 top_up 能力…現金版受限（DEFERRED）」段落記錄的是**代理→會員路徑**的當時結論，現金版 top_up 已改由**站長主錢包路徑**落地（見下 b.），故 DEFERRED 敘述僅存為歷史脈絡。

2026-06-27 一輪把 top_up 從信用版擴到現金版與 RF，9 站後台皆有可逆對稱測試。三條主線：

#### a. 信用版總代→代理 top_up（RC / RE / LT / RD PR#118 + RF PR#122）

補測後台階層的**最上層**（總代 → 下線代理），與既有「站長 → 會員」互補：

- **帳號層級**：使用站長層級帳號（`SITE_<ID>_DASHBOARD_USER`），皆**無 2FA**；`master_dashboard_page` fixture。
- **代理 tab 結構**：每個下線代理為 `.tab-item` 卡；卡內「存入」為 `btn-primary.me-2`、「提取」為 `:not(.me-2)`。
- **對稱驗證**：總代額度為 ∞，故**只驗代理側餘額**（存入 → 提取歸零，對稱可逆）。
- **`_agent_card` 定位**：tag-agnostic `.tab-item:has(:text-is(<account>))` —— RE / LT 代理名是 `<a>` 非 `<span>`，寫死 tag 會漏。
- **LT 166 代理分頁**：POM 先 `set_agent_page_size(500)` 把代理全載入 DOM，再定位卡片（否則分頁在 DOM 外找不到）。
- **RD 操作者密碼欄**：RD dialog 獨有「操作者密碼」欄位，POM 自動傳 `dashboard_pass`（`operator_password`）；其他站無此欄自動略過。
- **RF 站長即總代層級**：複用 `fresh_dashboard_page` 不需新 fixture；RF 自有 POM 加 `switch_to_agent_tab` / `deposit_to_agent` 等，代理 tab 同會員 `.tab-item` 結構，dialog 餘額讀 `label-xs[1]`，總代 ∞ 只驗代理側。

#### b. 現金版站長主錢包 top_up（LU PR#114 / LG·QW PR#116 / KS PR#117）

繞開「代理無點數」的 DEFERRED 卡點，改由**站長主錢包**對會員直接調整額度：

- **站長 login + TOTP 2FA**：會員管理 → Main wallet 金額彈窗 → 增 / 減，對稱可逆（`target=site_config.username`）。
- **LU 額度歷史稽核**：LU 另驗額度調整歷史（`#/report/balance-adjustment-report`），確認調整有落稽核紀錄。
- **KS 欄位錯位 quirk → 內容定位**：KS 後台少 Convenience Store 欄、Main wallet 在不同 `td` index 且 tbody / thead 未對齊（用固定 index 會誤命中 Create cell）。故 LU POM 的 `_wallet_amount_locator` 改用**內容定位**——鎖定「含 Game wallet 按鈕的 `td` 內 `div.bold`」，跨站通用，不寫死欄位 index。

#### c. LU 代理帳號 2026-06-25 起強制 2FA

- LU 代理帳號（如 `xxxx001`）自 2026-06-25 起**也強制 2FA**，conftest 需傳 `dashboard_agent_totp`（先前代理無 2FA）。
- LU 代理仍為 **read-only smoke**：點主錢包金額**不開彈窗**＝無充值權限，故只驗登入 / 導航 / logout，不做 top_up。

---

### 已覆蓋後台站台（2026-06-24 更新，8 站皆有代理測試）

代理後台依 UI 分兩種結構：**信用版 `/management`**（RC/RE/LT/RD，page object re-export RC）與
**現金版 Vue admin `/member`**（LU/LG/KS/QW，re-export LU）。

| 站台（代理） | 後台覆蓋 | 結構 / 備註 |
|------|---------|------|
| RC / RE / LT / RD | **top_up**（存入/提取 + balance 對稱驗證 + rollback） | 信用版；RD dialog 獨有「操作者密碼」欄位需傳 `operator_password`；代理額度由站長撥入 |
| LU / LG / KS | login + 導航 + logout **smoke** | 現金版 Vue admin，代理無 2FA |
| QW | login + 導航 + logout **smoke** | 現金版 Vue admin，**代理含 2FA**（驗證條件式 2FA 機制）|

> 站長層級（`-admin` + 2FA）目前僅 LU 有 login/導航/logout；其餘站站長層級尚未涵蓋。

### 後台 top_up 能力：信用版可做、現金版受限（2026-06-24 實測）

代理對「下屬會員」的金額異動入口，兩種結構不同，直接決定能否做 top_up 測試：

| 結構 | 入口 | top_up 可行性 |
|------|------|--------------|
| 信用版 `/management`（RC/RE/LT/RD） | 會員列「存入 / 提取」dialog | ✅ 站長撥額度給代理後即可；已落地對稱 top_up（RD 為範例）|
| 現金版 Vue admin（LU/LG/KS/QW） | 會員列「**Send points**」按鈕 | 🛑 **代理無點數時按鈕 `disabled`**；需站長「派點」給代理才解禁 |

- **現金版 top_up 目前 DEFERRED**：2026-06-24 實測 4 站（各已建 1 名測試會員）「Send points」**全部 disabled**，因代理帳號自身點數為 0。要啟用需站長階層派點給代理，屬額外測資前置，團隊評估暫不投入，故現金版維持 smoke。
- 未來要補現金版 top_up：站長派點給代理 → probe「Send points」dialog 結構 → 寫「代理→會員派點」對稱驗證（代理為 finite，可對稱驗 balance，不受站長 ∞ 額度影響）。
- 與「規則 7/8/9」（充值 cleanup、固定帳號、UI+API 雙驗）一致：現金版補做時同樣須可逆、雙重確認。

### 入口 URL 後綴：站長 vs 代理

後台同站有兩個入口，以 `-admin` 後綴區分**帳號層級**：

| 入口 | URL 形態 | 對應 config | 帳號層級 |
|------|---------|------------|---------|
| 站長 | `dev-<site>-**admin**-dashboard.<平台domain>` | `SITE_<X>_DASHBOARD_URL` | 站長（LU <LU 站長帳號>：∞ 額度、18 項頂層選單） |
| 代理 | `dev-<site>-dashboard.<平台domain>`（**無 -admin**） | `SITE_<X>_DASHBOARD_AGENT_URL` | 下級代理（LU `SITE_LU_DASHBOARD_AGENT_USER`，權限/選單較少） |

- **config 欄位**：`SiteConfig.dashboard_agent_url`（讀 `SITE_<X>_DASHBOARD_AGENT_URL`，PR #98 新增）。
  8 站 `.env.example` 已備欄位；**本機 `.env` 的代理 URL 待填**（站長 URL 去掉 `-admin` 即是）。
- ⚠️ dev 環境目前 `-admin` 站長入口**代理帳號也進得去**（站點端存取控制鬆動，屬 product/backend 問題，非測試碼）；代理層級測試仍應走「無 -admin」正規代理入口。

### LU 代理層級實作（2026-06-15 probe + 測試）

實機 probe 確認的代理（<LU 代理帳號>）與站長差異 → 已落地 `test_dashboard_agent.py`：

| 面向 | 站長 <LU 站長帳號> | 代理 <LU 代理帳號> |
|------|---------------|----------------|
| 2FA | 有 modal（TOTP） | **無**，帳密直接進 |
| 登入落點 | `#/dashboard/index` | `#/member/member-management` |
| 頂層選單 | 18 項 | **5 項**：`/member`、`/agent`、`/report`、`/report-bet-count`、`/statistical-report` |
| 側欄 | `.sidebar hide`（收合、viewport 外） | `.sidebar`（可見、子選單需展開） |
| 葉節點 | `a[href^='#/...']`（DOM 常駐） | **無 href**（`div.collapse-li-text`，Vue @click）|

- **登入碼共用、條件式分流**：`DashboardLoginPage._fill_totp` 改為**短 timeout（4s）偵測 `.dialog-container`**，沒出現即跳過 → 同一 `login()` 同時支援站長（有 2FA）與代理（無 2FA，`totp_secret` 不傳）。`verify_login_success` 改以「側欄出現」為共同成功信號（不綁落點 URL）。
- **導航分兩法**：站長用 `ManagementPage.navigate(route_substr)`（href + dispatch）；代理用 `navigate_agent(parent_id)`（展開父選單 → 結構定位無 href 葉節點 → dispatch）。
- **fixture 隔離**：`agent_dashboard_page` / `go_agent_dashboard`（讀 `dashboard_agent_url/user/pass`，獨立 context）；站長 `dashboard_page` / `go_dashboard` 不動。兩帳號不同、同 session 並存不互踢。
- **存提仍 defer**：<LU 代理帳號> 為空帳號（0 會員 / 0 餘額 / 0 銀行卡、提款鈕灰掉），無法做可逆對稱 balance 驗證（同 ∞ 站長卡點的另一面）；待有測資的代理帳號再補 deposit/withdraw。
- 代理錢包頁 `#/userInfo/agent-wallet`（在右上 user 下拉的 Wallet，非側欄）含 BalanceAdjustment Add/Reduce + Credit limit 操作，未來存提實作的入口參考。

### 其餘待辦
- **現金版 top_up**（LU/LG/KS/QW）：DEFERRED，見上「後台 top_up 能力」節。
- **站長層級**：除 LU 外其餘站站長層級（`-admin` + 2FA）尚未做；RE 站長目前無 2FA、KS 站長有「首次 2FA 送出被丟棄、需重送一次」的站點 quirk（onboard 時 login 要加一次性重試）。

---

## Browser Context 分離

### 規則 3：前後台必須使用獨立 browser context

後台和前台是不同 domain（見 .env `SITE_LT_DASHBOARD_URL` vs `SITE_LT_URL`）。
共用 context 會造成 cookie 衝突，驗證授權或登入狀態時會互相干擾。

#### 建議做法

```python
# 後台專用 fixture
@pytest.fixture(scope="session")
def dashboard_page(browser, site_config):
    context = browser.new_context()  # 獨立 context
    page = context.new_page()
    ...
    yield page
    context.close()
```

### 規則 4：跨前後台 e2e 測試需兩個 context + 兩個帳號

如「後台充值 → 前台驗證餘額」類型的 e2e 測試：
- 後台用管理員帳號（dashboard_user），獨立 context
- 前台用會員帳號（username），獨立 context
- **不可重複使用同一帳號** — 見規則 5

---

## Session 管理

### 規則 5：同帳號不可同時出現在多個 pytest process

後端實作「從其他裝置登入」機制：同一帳號在不同 client 登入時，**先登入的 session 會被踢掉**，後續 API 呼叫回傳 HTTP 401 PermissionDenied。

#### 實際影響
- 同帳號 API 測試 + UI 測試並行 → 一個一定會失敗
- 兩個 pytest process 都跑 LT → 後啟動的會踢掉前者

#### 規範
- **並行策略**：RC + LT 可並行（不同帳號），同站不同 process **禁止並行**
- **跨前後台測試**：前台用 member 帳號、後台用 admin 帳號，彼此獨立

---

## Fixture Scope 策略

### 規則 6：Dashboard `page` fixture 建議 session-scoped

後台登入有 TOTP 30 秒輪轉成本，若每個 test 都重新登入會大幅拖慢測試執行。

| Scope | 適用情境 |
|-------|---------|
| `session` | 整個測試跑一次登入（**建議預設**） |
| `class` | 需要隔離的測試群組（少見） |
| `function` | 僅在測試本身要驗證登入流程時使用 |

配合 `function-scoped` 的 `go_management` fixture，每個 test 起點一致。

```python
@pytest.fixture(scope="session")
def dashboard_page(browser, site_config):
    context = browser.new_context()
    page = context.new_page()
    login_page = DashboardLoginPage(page, site_config)
    login_page.goto_login()
    login_page.login()
    page.wait_for_url("**/management/**")
    yield page
    context.close()

@pytest.fixture(scope="function")
def go_management(dashboard_page, site_config):
    """每個 test 前回到管理頁"""
    dashboard_page.goto(
        f"{site_config.dashboard_url}#/management/all-management"
    )
```

---

## 現金版 Main wallet 彈窗的三種模式（2026-08-10 probe）

彈窗 `select` 有三個：`[0]` = Deposit/Withdrawal 模式、`[1]` = Platform bank、`[2]` = Member bank。

| 模式 | value | 行為 | 稽核落點 |
|------|-------|------|---------|
| Amount adjustment increased | `1` | 直接加額度 | `#/report/balance-adjustment-report`（type `Credit adjustment increased`） |
| Amount adjustment reduce | `2` | 直接減額度 | 同上（`Credit adjustment reduced`） |
| **General deposit（一般存款）** | `3` | 加額度；選取後**非同步回填 Platform bank** 下拉（dev 環境 3 個渠道，自動預選第一項＝後台補單渠道），Member bank 維持 None | 🛑 **無任何紀錄**（見下） |

**送出前必須等 Platform bank 回填**：`select[1]` 在模式切換前選項為空，切到 `3` 後才由後台渠道設定填入。POM `adjust_main_wallet()` 對 `mode="deposit"` 會 `wait_for_function(el => el.options.length > 0)` 後才 Confirm，否則會在渠道未定時送出。

> ⚠️ **General deposit 是稽核斷點（產品 bug 清單 #13）**：實測存款 +1 使餘額 1000→1001（由後續額度調整紀錄的 `Starting balance = 1001` 獨立佐證），但以唯一 remark token 搜遍 9 個金流頁（`wallet-history` / `balance-adjustment-report` / `member-deposit` 報表與審核頁 / `member-deposit-payment-report` / `memberPointRecord` / `member-deposit-store`）**全數 0 命中**。同彈窗的 `increase` / `reduce` 都有留痕 → 不是報表整體失效，是 General deposit 這條路徑漏寫紀錄。守門：`tests/dashboard/{lu,lg,qw}/test_general_deposit.py::TestGeneralDepositAudit`（xfail strict，修好自動 XPASS）。

## 測試資料管理

### 規則 7：充值後必須 cleanup 歸零

存入額度若不提取歸零，會累積影響後續測試的餘額斷言與報表資料。

```python
def test_deposit_and_verify(self, dashboard_page, site_config):
    mgmt = ManagementPage(dashboard_page)
    mgmt.switch_to_member_tab()
    mgmt.search_member(site_config.username)

    before = mgmt.get_member_balance(site_config.username)
    mgmt.deposit(site_config.username, amount=100)
    after = mgmt.get_member_balance(site_config.username)
    assert after == before + 100

    # Cleanup：提取歸零
    mgmt.withdraw(site_config.username, amount=100)
```

### 規則 8：固定測試帳號優於動態建立

- **不建議**：每個 test 建立新會員 → 跑完刪除
  - 資料污染、測試較慢、權限操作需管理員層級（root level 有 disabled 限制）
- **建議**：使用固定測試帳號（RC `norman001` / LT `dlttest01`），透過 cleanup 維持狀態一致

---

## 充值驗證雙重確認

### 規則 9：餘額驗證採「UI + API」雙重確認

| 驗證方式 | 用途 |
|---------|------|
| 後台會員列表額度欄位 | UI 即時驗證（主要）|
| API 查詢餘額 | 資料層 double check（防 UI 快取/延遲問題）|
| 前台登入查看錢包 | **現金版三站已落地**：`tests/dashboard/{lu,lg,qw}/test_frontend_balance_sync.py` |

僅用 UI 驗證可能漏掉後端 cache 或 UI 同步延遲問題。

**跨前後台 e2e 實作要點（2026-08-10）**：

- 前台用 root conftest 的 `class_logged_in_page`（`tests/dashboard/<site>/conftest.py` 已把 `site_config` 指向本站，故不必另建 fixture）；後台用 session `dashboard_page`。**兩者是不同帳號**（會員 vs 站長），不觸發同帳號互踢。
- 目標會員即前台帳號本人（`site_config.username`）。三站實測皆可在站長後台會員管理搜到 —— 注意 LU 的 `SITE_LU_DASHBOARD_TARGET_MEMBER` 是**另一個**會員，跨前後台測試不可沿用。
- 前台餘額是非同步取得，`reload()` 後直接讀會拿到舊值 → 用 `wait_helpers.wait_for_text_matches` 等目標數字出現再讀。
- **千分位格式各站不一**（實測 LG 顯示 `1001` 無逗號），比對 pattern 須把逗號設為選擇性（`",?".join(digits)`），否則會誤判成「前台沒同步」。

---

## 相關文件

- `docs/lt-dashboard-sitemap.md` — LT 後台功能地圖（路由、欄位、操作）
- `docs/testing-strategy.md` — 測試分層與執行規範
- `CLAUDE.md` — 前台測試撰寫慣例（互動、selector、exception handling）
