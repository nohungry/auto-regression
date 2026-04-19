"""
後台登入頁面 Page Object — LT 站點

目前 LT 後台與 RC 後台共用同一套 Vue 框架，selector 與流程相同，
因此 re-export RC 實作以保留 LT 獨立命名空間，未來若 LT 後台出現差異
（例如增加 TOTP、不同登入欄位），可直接在本檔案改為 subclass 覆寫。
"""

from pages.dashboard.rc.login_page import DashboardLoginPage

__all__ = ["DashboardLoginPage"]
