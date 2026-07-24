"""
後台登入頁面 Page Object — RE 站點 (BeWin)

RE 後台與 RC 共用同一套信用版後台（同平台） DOM 結構與登入流程，
因此 re-export RC 實作（含條件式 2FA：有 totp_secret 才填、無則跳過），
以保留 RE 獨立命名空間。未來若 RE 後台出現差異，可改為 subclass 覆寫。
"""

from pages.dashboard.rc.login_page import DashboardLoginPage

__all__ = ["DashboardLoginPage"]
