"""
後台管理頁面 Page Object — RD 站點（狗狗娛樂城）

RD 後台與 RC 後台共用同一套信用版 /management 框架，selector 與流程相同，
因此 re-export RC 實作以保留 RD 獨立命名空間。未來若 RD 後台出現差異
（例如不同 dialog 結構、不同 tab 命名），可改為 subclass 覆寫。

已知站點差異透過 method 參數處理（如 deposit/withdraw 的 operator_password=None
表示 RD dialog 無密碼欄位）。
"""

from pages.dashboard.rc.management_page import ManagementPage

__all__ = ["ManagementPage"]
