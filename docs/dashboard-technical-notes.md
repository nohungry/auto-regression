# 後台 Dashboard 測試技術注意事項

> 最後更新：2026-06-12
> 適用範圍：所有後台（dashboard）自動化測試

本文件整理後台測試撰寫時容易踩坑的技術規則。功能地圖請見 `docs/lt-dashboard-sitemap.md`。

---

## TOTP 2FA 登入流程

> **實作現況（2026-06-12）**：RC / RE / LT 後台目前皆為純帳密登入（LT login_page 只是
> re-export RC，無 TOTP）。**LU（Dlu測試站）是第一個真正把 TOTP 2FA 寫進登入流程的站**，
> 共用碼集中在 `utils/totp_helper.py`（pyotp 產碼），站台實作在 `pages/dashboard/lu/login_page.py`。

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

實機 probe（2026-06-12，站長 autolu001）。LU 後台 Vue hash SPA，與 RC/RE 不同框架：

- **側欄 `.sidebar.hide`（收合/移出畫面）** → 所有側欄連結在 viewport 外，**必須
  `dispatch_event("click")`**（仿 RC CSS-hidden sidebar，見本檔「元素互動例外」精神）。
- 頂層選單 `.sidebar-nav li.parent-li`（站長 18 項）；父項錨點 `a.memberSpan` 帶
  `id`=route（如 `id="/member"`），**locale-agnostic 穩定 selector**。
- 葉節點 `a[href^='#/...']`（如 `#/member/member-registration`）即使側欄收合仍在 DOM，
  可直接 dispatch 導航。導航判定：URL hash 變化 + `.app-main-content` 可見（不綁文案，
  後台 locale 混雜英文 + 未翻譯 i18n key）。
- **logout**：點右上 `.user-account`（顯示帳號）開下拉選單 → `Reset Password / Wallet /
  Agent Information / Logout` → 點 `Logout`（`get_by_role("link", name="Logout")`）→ 回 `#/login`。
- ⚠️ **帳號層級**：目前以站長帳號驗證（可見 18 項選單）；後續下級代理帳號
  （`SITE_LU_DASHBOARD_AGENT_USER`）權限不同，需另立代理層級測試。

---

## Browser Context 分離

### 規則 3：前後台必須使用獨立 browser context

後台和前台是不同 domain（`dev-lt-dashboard.t9platform.com` vs `dev-lt.t9platform.com`）。
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
| 前台登入查看錢包 | 留給跨前後台 e2e 測試（較重）|

僅用 UI 驗證可能漏掉後端 cache 或 UI 同步延遲問題。

---

## 相關文件

- `docs/lt-dashboard-sitemap.md` — LT 後台功能地圖（路由、欄位、操作）
- `docs/testing-strategy.md` — 測試分層與執行規範
- `CLAUDE.md` — 前台測試撰寫慣例（互動、selector、exception handling）
