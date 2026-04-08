# 多語系文案對照表

本文件為各站台測試斷言使用的文案來源，對應 `tests/<site>/feature/i18n/` 下的測試案例。

---

# DLT 站台

DLT 站台（dev-lt.t9platform.com）支援五種語系：繁中（tw）、簡中（cn）、英文（en）、泰文（th）、越文（vn）。  
語系切換方式：注入 `i18n_redirected_lt` cookie（`utils/locale_helper.set_locale()`）。

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

## DLT Selector 備註

| 元素 | Selector | 說明 |
|------|----------|------|
| 投注紀錄圖示 | `img[src*="betting-details"]` | src 不隨語系變動 |
| 會員訊息圖示 | `img[src*="member-messages"]` | src 不隨語系變動 |
| 投注紀錄文字 | `img[src*="betting-details"] > .. > p` | sibling p |
| 會員訊息文字 | `img[src*="member-messages"] > .. > p` | sibling p |
| 維護時間按鈕 | `button[class*='mb-5']` | 位於登出按鈕上方，具唯一 mb-5 margin |
| 登入按鈕 | `page.locator("button").first` | CSS-based，適用所有語系 |

---

# DRC 站台

DRC 站台（dev-drc.t9platform-ph.com）支援六種語系：繁體中文、簡体中文、日本語、ภาษาไทย、Tiếng Việt、English。  
語系切換方式：點擊 globe icon（`img[src*='global']`）→ 選擇語系名稱（`p.whitespace-nowrap`）。

> **注意**：DRC 比 DLT 多一個語系（日本語）。

## 首頁 Nav 文案（DRC-I18N-HOME-001~006）

測試檔：`tests/drc/feature/i18n/test_home_locale.py`

| 語系 | 首頁 | 真人 | 電子 | 捕魚 | 登入 |
|------|------|------|------|------|------|
| 繁體中文 | 首頁 | 真人 | 電子 | 捕魚 | 登入 |
| 簡体中文 | 首页 | 真人 | 电子 | 捕鱼 | 登录 |
| 日本語 | トップ | ライブ | 電子 | フィッシング | ログイン |
| ภาษาไทย | หน้าแรก | ถ่ายทอดสด | อิเล็กทรอนิกส์ | เกมยิงปลา | เข้าสู่ระบบ |
| Tiếng Việt | Trang đầu | Người thật | Điện tử | Câu cá | Đăng nhập |
| English | Home | Live Casino | Slots | Fishing | Login |

---

## 登入 Modal 文案（DRC-I18N-LOGIN-001~006）

測試檔：`tests/drc/feature/i18n/test_login_locale.py`

> DRC 登入為 **Modal 形式**（非獨立頁面），欄位用 `placeholder` 識別（非 label）。

| 語系 | 帳號 placeholder | 密碼 placeholder | 送出按鈕 |
|------|----------------|----------------|---------|
| 繁體中文 | 用戶名 | 密碼 | 登入 |
| 簡体中文 | 用户名 | 密码 | 登录 |
| 日本語 | ユーザー名 | パスワード | ログイン |
| ภาษาไทย | ชื่อผู้ใช้ | รหัสผ่าน | เข้าสู่ระบบ |
| Tiếng Việt | Tên người dùng | Mật khẩu | Đăng nhập |
| English | Username | Password | Login |

---

## 側邊欄文案（DRC-I18N-SIDEBAR-001~006）

測試檔：`tests/drc/feature/i18n/test_sidebar_locale.py`

> 對應 DLT 的 hamburger drawer。Sidebar container 為 CSS `width=0`（隱藏），但文字仍在 DOM 中，用 `body.to_contain_text()` 驗證。

| 語系 | 個人資訊 | 遊戲明細 | 站內信 |
|------|---------|---------|-------|
| 繁體中文 | 個人資訊 | 遊戲明細 | 站內信 |
| 簡体中文 | 个人信息 | 游戏明细 | 站内信 |
| 日本語 | 個人情報 | ゲーム履歴 | サイト内メール |
| ภาษาไทย | ข้อมูลส่วนตัว | รายละเอียดเกม | กล่องข้อความ |
| Tiếng Việt | Thông tin cá nhân | Chi tiết trò chơi | Thư nội bộ |
| English | Profile | Game History | Inbox |

---

## DRC Selector 備註

| 元素 | Selector | 說明 |
|------|----------|------|
| Globe icon | `img[src*='global']` | 語系切換入口 |
| 語系選項 | `p.whitespace-nowrap` | 語系名稱選項 |
| 登入觸發 / 送出按鈕 | `button.primary-btn` | CSS-based，適用所有語系 |
| 帳號欄位 | `input.input-style[type='text']` | placeholder 隨語系變動 |
| 密碼欄位 | `input.input-style[type='password']` | placeholder 隨語系變動 |
| Sidebar 項目 | `.sidebar-item` | DOM 中有文字，CSS width=0 隱藏 |
