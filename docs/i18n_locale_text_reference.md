# DLT 多語系文案對照表

DLT 站台（dev-lt.t9platform.com）支援五種語系：繁中（tw）、簡中（cn）、英文（en）、泰文（th）、越文（vn）。  
本文件為測試斷言使用的文案來源，與 `tests/dlt/feature/i18n/` 下的測試案例對應。

---

## 首頁 Nav 文案（WIN-I18N-001~005）

測試檔：`tests/dlt/feature/i18n/test_home_locale.py`

| 語系 | 熱門 | 真人 | 電子 | 捕魚 | 登入 |
|------|------|------|------|------|------|
| tw（繁中） | 熱門 | 真人 | 電子 | 捕魚 | 登入 |
| cn（簡中） | 热门 | 真人 | 电子 | 捕鱼 | 登录 |
| en（英文） | Hot | Live Casino | Slots | Fishing | Login |
| th（泰文） | ยอดฮิต | คนจริง | อิเล็กทรอนิกส์ | ยิงปลา | เข้าสู่ระบบ |
| vn（越文） | Phổ biến | Người thật | Điện tử | Câu cá | Đăng nhập |

---

## 登入頁文案（WIN-I18N-LOGIN-001~005）

測試檔：`tests/dlt/feature/i18n/test_login_locale.py`

| 語系 | 帳號欄位標籤 | 密碼欄位標籤 | 登入按鈕 |
|------|------------|------------|---------|
| tw（繁中） | 會員帳號 | 登入密碼 | 登入 |
| cn（簡中） | 会员帐号 | 登录密码 | 登录 |
| en（英文） | Username | Password | Login |
| th（泰文） | บัญชีสมาชิก | รหัสผ่านเข้าสู่ระบบ | เข้าสู่ระบบ |
| vn（越文） | Tài khoản thành viên | Mật khẩu đăng nhập | Đăng nhập |

> **已知行為**：「先去逛逛」按鈕在所有語系均固定顯示繁中，未隨語系翻譯。

---

## 會員 Drawer 選單文案（WIN-I18N-DRAWER-001~005）

測試檔：`tests/dlt/feature/i18n/test_drawer_locale.py`

| 語系 | 投注紀錄 | 會員訊息 | 維護時間／存款 |
|------|---------|---------|--------------|
| tw（繁中） | 投注紀錄 | 會員訊息 | 維護時間 |
| cn（簡中） | 投注记录 | 会员讯息 | 维护时间 |
| en（英文） | Betting Record | Member Messages | Maintenance Time |
| th（泰文） | ประวัติการเดิมพัน | ข้อมูลสมาชิก | ช่วงเวลาบำรุงรักษา |
| vn（越文） | Lịch sử cược | Tài khoản | Bảo trì |

> **說明**：  
> - 「維護時間／存款」欄位為同一按鈕，存款功能開放時顯示「存款」，維護期間顯示「維護時間」。  
> - Drawer 開啟方式使用 locale-agnostic selector（`img[src*="betting-details"]`），不依賴文案等待，避免非繁中語系 timeout。

---

## Selector 備註

| 元素 | Selector | 說明 |
|------|----------|------|
| 投注紀錄圖示 | `img[src*="betting-details"]` | src 不隨語系變動 |
| 會員訊息圖示 | `img[src*="member-messages"]` | src 不隨語系變動 |
| 投注紀錄文字 | `img[src*="betting-details"] > .. > p` | sibling p |
| 會員訊息文字 | `img[src*="member-messages"] > .. > p` | sibling p |
| 維護時間按鈕 | `button[class*='mb-5']` | 位於登出按鈕上方，具唯一 mb-5 margin |
| 登入按鈕 | `page.locator("button").first` | CSS-based，適用所有語系 |
