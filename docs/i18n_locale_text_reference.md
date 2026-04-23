# 多語系文案對照表

本文件為各站台測試斷言使用的文案來源，對應 `tests/<site>/feature/i18n/` 下的測試案例。

---

# LT 站台

LT 站台（SITE_LT_URL）支援五種語系：繁中（tw）、簡中（cn）、英文（en）、泰文（th）、越文（vn）。  
語系切換方式：注入 `i18n_redirected_lt` cookie（`utils/locale_helper.set_locale()`）。

---

> **WAP 改版後 i18n 覆蓋現況（2026-04-23）**：
> - ✅ **登入頁 input placeholder** 有完整 5 語系翻譯
> - ✅ **`/member-center` 按鈕與 section heading** 有完整 5 語系翻譯
> - ❌ **首頁 nav**（`.cat-btn`、底部 tabbar）所有語系固定繁中，未套 i18n
> - ❌ **登入頁按鈕**（`btn-login` / `btn-browse`）、**lang-text** 語系切換文案固定繁中
>
> 下表僅列出「測試目前實際驗證」的項目；已 skip 或固定繁中的項目另列說明。

---

## 首頁 Nav 文案（WIN-I18N-001~005）— 全 skip

測試檔：`tests/lt/feature/i18n/test_home_locale.py`（`pytestmark.skip`）

WAP 首頁 `.cat-btn`（遊戲大廳/我的最愛/台灣真人/國際真人/更多）與底部 tabbar（維護/公告/排行榜/個人）在所有語系下固定繁中，i18n 尚未套到首頁 nav 層。待產品端實作後再 un-skip。

---

## 登入頁 placeholder 文案（WIN-I18N-LOGIN-001~005）

測試檔：`tests/lt/feature/i18n/test_login_locale.py`

WAP `input.login-input` 帳號/密碼欄位 placeholder 為關鍵字包含驗證（非全字比對，避免半形/全形空格差異）：

| 語系 | 帳號欄位 placeholder 關鍵字 | 密碼欄位 placeholder 關鍵字 |
|------|---------------------------|---------------------------|
| tw（繁中） | 請填寫 | 請填寫 |
| cn（簡中） | 请填写 | 请填写 |
| en（英文） | Please enter | Please enter |
| th（泰文） | กรุณากรอก | กรุณากรอก |
| vn（越文） | Vui lòng điền | Vui lòng điền |

> **已知產品現況（非 bug）**：
> - `button.btn-login` 固定「立即登入」，所有語系不變
> - `button.btn-browse` 固定「先去逛逛」，所有語系不變
> - `span.lang-text` 左上語系切換文案固定「繁中」，所有語系不變 — 對應 `TestI18NLangSwitcher.test_lang_text_reflects_locale` 以 `xfail(strict=True)` 標記，產品端修正後會 XPASS 並觸發失敗提醒拿掉 xfail

---

## /member-center 文案（WIN-I18N-MC-001~005）

測試檔：`tests/lt/feature/i18n/test_member_center_locale.py`

WAP 改版後「會員 drawer」已作廢，改為獨立 `/member-center` 頁面。4 項核心文案皆有完整 5 語系翻譯：

| 語系 | 維護時間 | 登出 | 投注紀錄 | 會員訊息 |
|------|---------|------|---------|---------|
| tw（繁中） | 維護時間 | 登出 | 投注紀錄 | 會員訊息 |
| cn（簡中） | 维护时间 | 登出 | 投注记录 | 会员讯息 |
| en（英文） | Maintenance Time | Logout | Betting Record | Member Messages |
| th（泰文） | ช่วงเวลาบำรุงรักษา | ออกจากระบบ | ประวัติการเดิมพัน | ข้อมูลสมาชิก |
| vn（越文） | Bảo trì | Đăng xuất | Lịch sử cược | Tài khoản |

> **說明**：
> - 「維護時間」按鈕為存款功能槽位佔位（LT 為信用板站點無存款流程，見 `memory/project_lt_credit_site.md`）；dev 環境顯示為維護時間文案。
> - 進入 /member-center 的 bottom tabbar「個人」tab 在所有語系固定繁中（非 i18n），selector `has_text="個人"` 為 locale-agnostic-in-effect。

---

## LT Selector 備註（WAP）

| 元素 | Selector | 說明 |
|------|----------|------|
| 登入頁帳密欄位 | `input.login-input` | 雙 input 透過 `nth(0)`/`nth(1)` 區分；placeholder 有 i18n |
| 登入送出按鈕 | `button.btn-login` | 固定繁中「立即登入」 |
| 不登入逛逛按鈕 | `button.btn-browse` | 固定繁中「先去逛逛」 |
| navbar 信用額度 | `.bg-navbar p.text-amount` | 只驗非空，不寫死值 |
| navbar 登入狀態 pill | `.bg-navbar p.text-text-light-main` | 未登入顯示 `Not Login` / `尚未登入` 等；已登入顯示 username |
| 底部個人 tab | `.shadow-menubar .cursor-pointer[has-text="個人"]` | locale-agnostic-in-effect（所有語系固定繁中） |
| /member-center 信用額度 | `p.font-bold.text-amount` | 與 navbar 餘額同步 |
| /member-center 維護時間按鈕 | `button.bg-secondary.mb-5` | 唯一 mb-5 class，locale-agnostic |
| /member-center 登出按鈕 | `button.bg-secondary` 第 2 個（`.nth(1)`） | locale-agnostic；勿用 `has_text="登出"` 會 timeout en/th/vn |
| /member-center section heading | `p.font-bold` 搭 `has_text=<locale-specific>` | 投注紀錄/會員訊息 i18n 文案 |

---

# RC 站台

RC 站台（SITE_RC_URL）支援六種語系：繁體中文、簡体中文、日本語、ภาษาไทย、Tiếng Việt、English。  
語系切換方式：點擊 globe icon（`img[src*='global']`）→ 選擇語系名稱（`p.whitespace-nowrap`）。

> **注意**：RC 比 LT 多一個語系（日本語）。

## 首頁 Nav 文案（RC-I18N-HOME-001~006）

測試檔：`tests/rc/feature/i18n/test_home_locale.py`

| 語系 | 首頁 | 真人 | 電子 | 捕魚 | 登入 |
|------|------|------|------|------|------|
| 繁體中文 | 首頁 | 真人 | 電子 | 捕魚 | 登入 |
| 簡体中文 | 首页 | 真人 | 电子 | 捕鱼 | 登录 |
| 日本語 | トップ | ライブ | 電子 | フィッシング | ログイン |
| ภาษาไทย | หน้าแรก | ถ่ายทอดสด | อิเล็กทรอนิกส์ | เกมยิงปลา | เข้าสู่ระบบ |
| Tiếng Việt | Trang đầu | Người thật | Điện tử | Câu cá | Đăng nhập |
| English | Home | Live Casino | Slots | Fishing | Login |

---

## 登入 Modal 文案（RC-I18N-LOGIN-001~006）

測試檔：`tests/rc/feature/i18n/test_login_locale.py`

> RC 登入為 **Modal 形式**（非獨立頁面），欄位用 `placeholder` 識別（非 label）。

| 語系 | 帳號 placeholder | 密碼 placeholder | 送出按鈕 |
|------|----------------|----------------|---------|
| 繁體中文 | 用戶名 | 密碼 | 登入 |
| 簡体中文 | 用户名 | 密码 | 登录 |
| 日本語 | ユーザー名 | パスワード | ログイン |
| ภาษาไทย | ชื่อผู้ใช้ | รหัสผ่าน | เข้าสู่ระบบ |
| Tiếng Việt | Tên người dùng | Mật khẩu | Đăng nhập |
| English | Username | Password | Login |

---

## 側邊欄文案（RC-I18N-SIDEBAR-001~006）

測試檔：`tests/rc/feature/i18n/test_sidebar_locale.py`

> 對應 LT 的 hamburger drawer。Sidebar container 為 CSS `width=0`（隱藏），但文字仍在 DOM 中，用 `body.to_contain_text()` 驗證。

| 語系 | 個人資訊 | 遊戲明細 | 站內信 |
|------|---------|---------|-------|
| 繁體中文 | 個人資訊 | 遊戲明細 | 站內信 |
| 簡体中文 | 个人信息 | 游戏明细 | 站内信 |
| 日本語 | 個人情報 | ゲーム履歴 | サイト内メール |
| ภาษาไทย | ข้อมูลส่วนตัว | รายละเอียดเกม | กล่องข้อความ |
| Tiếng Việt | Thông tin cá nhân | Chi tiết trò chơi | Thư nội bộ |
| English | Profile | Game History | Inbox |

---

## RC Selector 備註

| 元素 | Selector | 說明 |
|------|----------|------|
| Globe icon | `img[src*='global']` | 語系切換入口 |
| 語系選項 | `p.whitespace-nowrap` | 語系名稱選項 |
| 登入觸發 / 送出按鈕 | `button.primary-btn` | CSS-based，適用所有語系 |
| 帳號欄位 | `input.input-style[type='text']` | placeholder 隨語系變動 |
| 密碼欄位 | `input.input-style[type='password']` | placeholder 隨語系變動 |
| Sidebar 項目 | `.sidebar-item` | DOM 中有文字，CSS width=0 隱藏 |
