"""
後台管理頁面 Page Object — LT 站點

目前 LT 後台與 RC 後台共用同一套 Vue 框架，selector 與流程相同，
因此 re-export RC 實作以保留 LT 獨立命名空間，未來若 LT 後台出現差異
（例如不同 dialog 結構、不同 tab 命名），可直接在本檔案改為 subclass 覆寫。

已知站點差異透過 method 參數處理（如 deposit/withdraw 的 operator_password=None
表示 LT dialog 無密碼欄位）。
"""

from pages.dashboard.rc.management_page import ManagementPage

__all__ = ["ManagementPage"]
