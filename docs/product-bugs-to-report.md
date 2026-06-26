# 待轉知產品/Luke 的站點 Bug 清單

> 本清單彙整**自動化測試攔截到、且已實機 probe 確認**的產品/後端缺陷。
> 每項皆由測試以 `xfail(strict)` 或 `skip` 守門 —— 產品修正後對應測試會自動 XPASS / 可 un-skip，形成回歸守門。
> 維護方式：產品修好一項就移除該列並 un-gate 對應測試。最後更新：2026-06-26。

## 一、確認的產品/前端 Bug（建議轉知產品修正）

| # | 站 | 問題 | 證據 / 實況 | 測試守門 | 嚴重度 |
|---|----|------|------------|---------|--------|
| 1 | **LT** | **首頁底部中央 footer tab 破損**：5 個 tab `[維護, 公告, (空), 排行榜, 個人]` 的**中間第 3 個 tab 圖示與文字都是空的** | probe 2026-06-26：該 tab icon 為 `<img src="" h=0>`（無 src/data-src），label 也空。應為中央主入口（如「遊戲大廳」）渲染壞掉 | `tests/lt/.../test_visual.py::test_home_no_broken_images`、`test_i18n_hydration.py::test_home_images_no_empty_src`（deterministic FAIL） | 中（首頁主導覽缺一個入口） |
| 2 | **LT** | **登入頁帳號欄 placeholder 文案錯**：顯示「請填寫8-20位的字母或數字」，應為帳號規則（4-10 位）。疑與密碼欄（8-20）複製錯誤 | probe 2026-06-26：username & password 兩欄 placeholder 完全相同 | `tests/lt/feature/copy/test_copy.py::test_login_username_placeholder`（xfail strict） | 低（文案） |
| 3 | **QW** | **首頁 `<title>` 誤掛「王老吉娛樂城」**（RC 站名），正確應為「LM來財娛樂城」。疑 RC 模板複製未改 | dev-qw 前台實測 | `tests/qw/feature/copy/test_copy.py::test_home_title`（xfail strict） | 中（SEO/品牌） |
| 4 | **RD** | **未登入點 sidebar 不會自動彈出登入 modal**（其他站有此 UX） | 實測未觸發登入彈窗 | `tests/rd/feature/sidebar/test_sidebar.py::test_sidebar_triggers_login`（xfail strict） | 低（UX 缺漏） |
| 5 | **LT** | **登入頁語系切換未套 i18n**：`span.lang-text` 及首頁 nav 所有語系固定繁中（cn/en/th/vn 未翻譯） | 實測切語系文案不變 | `tests/lt/feature/i18n/test_login_locale.py`（xfail）、`test_home_locale.py`（skip） | 中（多語系未完成） |
| 6 | **RE** | **navbar 餘額區未實作獨立 refresh 按鈕**（僅 coin icon + 數字 span） | 實機確認無刷新鈕 | `tests/re/feature/wallet/test_wallet.py::test_balance_refresh_button_visible`（skip） | 低（功能未做） |

## 二、確認的後端 Bug

| # | 站 | 問題 | 證據 | 測試守門 | 嚴重度 |
|---|----|------|------|---------|--------|
| 7 | **LT** | **`bet_record` API 回 500 InternalError**：同 token 打 `getBalance` 正常 200，唯獨此端點 500。疑後端額外 side-channel 檢查（IP 白名單 / TLS 指紋 / session cookie 綁定） | 帶完整瀏覽器 headers 仍重現 | `tests/api/lt/test_bet_record.py::test_get_bet_record`（xfail） | 中（API 自動化被擋） |

## 三、非產品 Bug — 測試端待穩定（我方處理，非轉知產品）

> 以下**不是站點 bug**，而是 LT Nuxt SPA 載入慢造成的測試 flaky，記此供團隊參考、避免誤判為產品問題。

- **LT 全 feature suite 多處 flaky**：`casino banner hidden`、`member panel timeout`、`wallet balance`、`member_center_locale[001-005]`、`betting_record_reference` —— 這些**單獨跑 / probe 皆正常**，只在 full suite 連續跑時因 timing race 偶發 fail。
- **根因**：LT SPA `networkidle`/`load` 偶爾 30s timeout、lazy 圖片載入慢。CI 的 `--reruns 1` 多半會在重試時通過（故 CI 未持續紅）。
- **處置方向（我方）**：對受影響測試加更穩健的等待（等關鍵元素而非 networkidle）/ 必要時標 `@pytest.mark.flaky`；已順手修 `pages/lt/login_page.py` 的 `goto()` 'load' timeout（改 domcontentloaded + networkidle fallback）。

## 引用
- LT 換版善後與站點現況：`pages/lt/`、`tests/lt/`
- 各 bug 的詳細 probe 紀錄：見對應測試檔 docstring 與 xfail/skip reason
