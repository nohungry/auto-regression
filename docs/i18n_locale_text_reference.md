# 多語系文案對照表

本文件為各站台測試斷言使用的文案來源，對應 `tests/<site>/feature/i18n/` 下的測試案例。

---

# LT 站台

> ⚠️ **待複驗（2026-07-24）**：LT 前台於 **2026-07** 發生**第三次換版**（目前觀望中）。本節 LT 文案對照以 **2026-05-19（desktop responsive 換版）版**為準；待換版收斂穩定後需**重新 probe 複驗**文案與 selector。RC / RD 段不受此影響。

LT 站台（SITE_LT_URL）支援五種語系：繁中（tw）、簡中（cn）、英文（en）、泰文（th）、越文（vn）。  
語系切換方式：注入 `i18n_locale` cookie（`utils/locale_helper.set_locale()`）。

---

> **desktop responsive 換版後 i18n 覆蓋現況（2026-05-19）**：
> - ✅ **登入頁 input placeholder** 有完整 5 語系翻譯（產品改了動詞 例：請填寫→請輸入，已用「該語系代表字」keyword 容錯）
> - ✅ **個人中心 panel 登出按鈕** + **底部 footer 維護 tab** 有完整 5 語系翻譯
> - ✅ **footer 個人 tab** 文字隨 locale 變化（cn=个人、en=Personal、th=ส่วนตัว、vn=Cá nhân）— 不可再用 `has_text="個人"` 寫死
> - ❌ **首頁 hero swipe sections** (`span.category-title`) 仍為繁中（來財獨家/爆分精選/活動專區），i18n 未覆蓋
> - ❓ **`span.lang-text`** 是否仍固定繁中尚未在新版重測，`TestI18NLangSwitcher.test_lang_text_reflects_locale` 仍以 `xfail(strict=True)` 守門
>
> 2026-04-23 i18n hydration regression 已修復（無 raw key、無 empty src img），原 14 個 xfail 守門全處理。

---

## 首頁 Nav 文案（WIN-I18N-001~005）— 全 skip

測試檔：`tests/lt/feature/i18n/test_home_locale.py`（`pytestmark.skip`）

換版後首頁分類 `.cat-btn` 消失，改為 hero swipe sections (`span.category-title`)，3 個 section title（來財獨家 / 爆分精選 / 活動專區）所有語系固定繁中。原 WAP 時期 5 分類 i18n 守門已無對應元素，整檔 skip 待產品定型新版分類互動模式後重設計。

---

## 登入頁 placeholder 文案（WIN-I18N-LOGIN-001~005）

測試檔：`tests/lt/feature/i18n/test_login_locale.py`

`input.input-style:not(.password-input)` / `input.password-input` placeholder 為**「該語系代表字」**驗證（產品 2026-05-18 換版動詞變動：請填寫→請輸入 / Please enter→Enter / Vui lòng điền→Vui lòng nhập，改用代表字可同時 cover 新舊）：

| 語系 | 帳號欄位 placeholder 關鍵字 | 密碼欄位 placeholder 關鍵字 |
|------|---------------------------|---------------------------|
| tw（繁中） | 請 | 請 |
| cn（簡中） | 请 | 请 |
| en（英文） | Enter | Enter |
| th（泰文） | กรุณา | กรุณา |
| vn（越文） | Vui lòng | Vui lòng |

> **已知產品現況**：
> - `button.base-btn.type1`（會員登入）/ `.type2`（先去逛逛）文案是否仍固定繁中尚未重新確認；本檔不驗
> - `span.lang-text` 左上語系切換文案在新版位置與行為待重新 probe，`TestI18NLangSwitcher` 仍以 `xfail(strict=True)` 守門

---

## 個人中心 panel + footer 維護文案（WIN-I18N-MC-001~005）

測試檔：`tests/lt/feature/i18n/test_member_center_locale.py`

2026-05-18 換版後：
- 個人中心改為 `.dialog-mask-full` SPA inline overlay panel（URL 不變，**無 /member-center 路由**）
- 維護時間從 panel 內按鈕搬到底部 footer 第一個 tab
- 「投注紀錄」「會員訊息」改為 panel 左側 slide-in `.sidebar-item.*` 結構，其 5 語系文案尚未重新 probe，本檔暫不驗

本檔目前只驗兩個**位置與 5 語系翻譯都已確認**的元素：

| 語系 | footer 維護 tab | panel 登出按鈕 |
|------|----------------|----------------|
| tw（繁中） | 維護 | 登出 |
| cn（簡中） | 维护 | 登出 |
| en（英文） | Maintenance | Logout |
| th（泰文） | ปิดปรับปรุง | ออกจากระบบ |
| vn（越文） | Bảo trì | Đăng xuất |

> **說明**：
> - th 維護文案實測為「ปิดปรับปรุง」（暫停服務）— 與原 WAP 時期「ช่วงเวลาบำรุงรักษา」不同
> - 「維護時間」按鈕為存款功能槽位佔位（LT 為信用板站點無存款流程）
> - 底部「個人」tab 在新版**有 i18n** — POM 改用結構 `.footer-bg .content` `.last` 取（不可再用 `has_text="個人"`）

---

## LT Selector 備註（desktop responsive，2026-05-18 換版後）

| 元素 | Selector | 說明 |
|------|----------|------|
| 登入頁帳號欄 | `input.input-style:not(.password-input)` | text input；placeholder 有 i18n |
| 登入頁密碼欄 | `input.password-input` | password input；placeholder 有 i18n |
| 登入送出按鈕 | `button.base-btn.type1` | 結構 selector；文案 i18n 變動，**禁用 `has_text`** |
| 不登入逛逛按鈕 | `button.base-btn.type2` | 結構 selector；同上 |
| 登入錯誤 dialog 確定 | `button.toast-confirm-btn` | ⚠️ 與全域 MutationObserver 撞 selector，LT conftest 必須不注入 observer |
| navbar 容器 | `.nav-bg-m` | 取代舊 `.bg-navbar` |
| navbar 信用額度 | `.coin-wrap-bg span` | 只驗非空，不寫死值 |
| navbar 帳號 pill | `.user-info-bg p.tip-single` | 已登入顯示 username |
| 未登入 navbar CTA | `div.login-btn-with-text` | 未登入時 navbar 右側「登入」 |
| 底部 footer 容器 | `.footer-bg` | 取代舊 `.shadow-menubar` |
| footer 各 tab | `.footer-bg .content` | 5 個 tab：`[0]維護 / [1]公告 / [2]中間 CTA / [3]排行榜 / [4]個人` |
| footer 個人 tab | `.footer-bg .content` `.last` | **不用 `has_text="個人"`**，文案會 i18n |
| footer 維護 tab | `.footer-bg .content` `.nth(0)` | 同上原則 |
| 個人中心 panel | `.dialog-mask-full` | UA dialog 與 member panel 共用，用 `.first/.last` 區分 |
| panel 登出按鈕 | `button.cancel-btn` filter `has_text="<locale 登出>"` | 文案有 i18n，需傳對應語系字串 |
| UA dialog 確定 | `.dialog-mask-full div[class*='cursor-pointer']` filter `has_text="確定"` | 容器是 div，需 `dispatch_event("click")` |
| 客服浮動按鈕 | `a.fixed-icon.fixed-telegram` | class 叫 telegram 但 href 仍是 LINE Official（`line.me/R/...`） |
| 登入完成判定 | `DLT` cookie 存在 | **不能用 page.url**（Nuxt pushState 不更新 url 對象） |
| 登入 click 時機 | `dispatch_event("click")` | Vue handler 攔截，raw `.click()` 不觸發 submit |

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

---

# RD 站台

RD 站台（SITE_RD_URL，狗狗娛樂城）支援五種語系：繁體中文、簡体中文、日本語、Tiếng Việt、English（**無泰語**，與 RC/RE 6 語系不同）。
語系切換方式：點 navbar 上「顯示當前語言」的按鈕（`button.bg-shade03`）→ 從下拉選單（`div.cursor-pointer p`）選擇目標語系。

> **與 RC 不同**：RD 沒有 globe icon，語系觸發按鈕直接顯示當前語言名稱。click handler 因 SPA hydration 必須用 `dispatch_event("click")`，第一次失敗時等 ~2s 重試。

## 首頁登錄按鈕 + 6 分類文案（RD-I18N-HOME-001 ~ 005）

測試檔：`tests/rd/feature/i18n/test_home_locale.py`

**6 個分類順序**：電子 / 真人 / 捕魚 / 體育 / 彩票 / 鬥雞（RD 獨有 6 類，含彩票與鬥雞）。

| 語系 | 登錄按鈕 | 1.電子 | 2.真人 | 3.捕魚 | 4.體育 | 5.彩票 | 6.鬥雞 |
|------|---------|--------|--------|--------|--------|--------|--------|
| 繁體中文 | 登錄 | 電子 | 真人 | 捕魚 | 體育 | 彩票 | 鬥雞 |
| 簡体中文 | 登录 | **任意电子** ⚠️ | 真人 | 捕鱼 | 体育 | **任意彩票** ⚠️ | 斗鸡 |
| 日本語 | ログイン | eゲーム | ライブ | フィッシング | スポーツ | ロト | 闘鶏 |
| Tiếng Việt | Đăng nhập | Điện tử | Người thực | Bắn cá | Thể thao | xổ số | Đá gà |
| English | Login | Slots | Casino | Fishing | Sports | **Cockfight / Fighting rooster** ⚠️ | Cockfight |

> **As-is 慣例（dev-rd 翻譯已知問題，本測試以當前文案為準，產品修正後 test fail = i18n regression 訊號）**：
> - **簡体中文**：「电子」/「彩票」分類顯示為「任意电子」/「任意彩票」（i18n key 未對齊，誤用 "任意 X" 變體）
> - **English**：第 5 格（彩票/lottery）顯示為「Cockfight / Fighting rooster」（漏翻 / key 重用 cockfighting）；第 6 格才是預期的 "Cockfight"

---

## 登入 Modal 文案（RD-I18N-LOGIN-001 ~ 005）

測試檔：`tests/rd/feature/i18n/test_login_locale.py`

| 語系 | 帳號 placeholder | 密碼 placeholder | 送出按鈕 |
|------|-----------------|-----------------|---------|
| 繁體中文 | 帳號 | 密碼 | 登錄 |
| 簡体中文 | **帳號** ⚠️ | 密码 | 登录 |
| 日本語 | アカウント | パスワード | ログイン |
| Tiếng Việt | Tài khoản | Mật khẩu | Đăng nhập |
| English | User Name | Password | Login |

> **As-is 慣例**：簡体中文 username placeholder 為「帳號」（與其他繁體欄位混用），看似翻譯遺漏。若產品端修為「账号」則此測試會 fail，視為 i18n regression 訊號。

---

## 側邊欄前 3 項文案（RD-I18N-SIDEBAR-001 ~ 005）

測試檔：`tests/rd/feature/i18n/test_sidebar_locale.py`

> RD 側邊欄文字節點為 `p.opacity-0.lg:hidden`（lg viewport 上 `display:none`，但 DOM 中仍存在）。  
> 用 `body.to_contain_text()` 驗證（不需 hover / scroll，與 RC 同 pattern）。

| 語系 | 個人資訊 | 遊戲明細 | 站內信 |
|------|---------|---------|-------|
| 繁體中文 | 個人資訊 | 遊戲明細 | 站內信 |
| 簡体中文 | **我的帳戶** ⚠️ | 游戏记录 | 信件 |
| 日本語 | マイアカウント | ゲーム履歴 | メール |
| Tiếng Việt | Tài khoản của tôi | Lịch sử trò chơi | Thư |
| English | My Account | Game records | Member message |

> **As-is 慣例（簡体中文「我的帳戶」用繁體「帳」字，應為「账」；mixed 繁/簡 為已知 i18n bug，產品修正後 test fail = regression 訊號）**

---

## 語系下拉選單（RD-TC-L01）

測試檔：`tests/rd/feature/i18n/test_language_dropdown.py`

驗證 navbar 語言下拉選單包含 5 個語系（繁體中文 / 簡体中文 / English / Tiếng Việt / 日本語），無泰語。

---

## RD Selector 備註

| 元素 | Selector | 說明 |
|------|----------|------|
| 語系觸發按鈕 | `button.bg-shade03` | navbar 顯示當前語言；filter 用 LANG names regex 鎖定 |
| 語系選項 | `div.cursor-pointer p` | dropdown 內各語系名稱 |
| 登錄按鈕 | `button.neon-btn` | navbar 主按鈕（has_text="登錄"），用以區分其他主按鈕 |
| 登入 Modal 帳密欄位 | `input` 第 0/1 個（nth(0)/nth(1)） | placeholder 隨語系變動 |
| 登入 Modal 送出 | `button.main-btn` + has_text=login_text | 送出按鈕，文案隨語系變動 |
| 公告蓋板 | `.dialog-mask` | 切語系前必須先 dismiss，否則 navbar 點擊會被攔截 |
| 互動模式 | `dispatch_event("click")` | SPA hydration race + dialog-mask 攔截，普通 click 失效 |
