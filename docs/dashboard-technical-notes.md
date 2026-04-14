# 後台 Dashboard 測試技術注意事項

> 最後更新：2026-04-14
> 適用範圍：所有後台（dashboard）自動化測試

本文件整理後台測試撰寫時容易踩坑的技術規則。功能地圖請見 `docs/lt-dashboard-sitemap.md`。

---

## TOTP 登入流程

### 規則 1：OTP input 必須用 native value setter

後台登入的 TOTP 驗證 input（`input.otp-hidden-input`）是自訂 React component。
一般 `page.fill()` / `page.type()` **無法觸發 React state 更新**，會導致登入卡在 OTP modal。

#### 正確做法

```python
import pyotp

totp_code = pyotp.TOTP(site_config.dashboard_totp).now()
page.evaluate("""(code) => {
    const input = document.querySelector('input.otp-hidden-input');
    const setter = Object.getOwnPropertyDescriptor(
        window.HTMLInputElement.prototype, 'value').set;
    setter.call(input, code);
    input.dispatchEvent(new Event('input', { bubbles: true }));
}""", totp_code)
```

### 規則 2：TOTP 30 秒輪轉必須預留緩衝

TOTP 每 30 秒輪轉一次，若 code 在提交瞬間過期會驗證失敗。

#### 建議做法

```python
def get_totp_with_buffer(secret: str, min_remaining: int = 5) -> str:
    """確保 OTP 至少還有 min_remaining 秒有效期"""
    import pyotp, time
    totp = pyotp.TOTP(secret)
    remaining = totp.interval - (time.time() % totp.interval)
    if remaining < min_remaining:
        time.sleep(remaining + 1)  # 等到下一個週期
    return totp.now()
```

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
