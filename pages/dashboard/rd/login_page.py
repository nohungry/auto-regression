"""
後台登入頁面 Page Object — RD 站點（狗狗娛樂城）

RD 後台與 RC 共用同一套 t9platform 信用版後台 DOM 結構與登入流程，
因此 re-export RC 實作（含條件式 2FA：有 totp_secret 才填、無則跳過），
以保留 RD 獨立命名空間。未來若 RD 後台出現差異，可改為 subclass 覆寫。
"""

from pages.dashboard.rc.login_page import DashboardLoginPage

__all__ = ["DashboardLoginPage"]
