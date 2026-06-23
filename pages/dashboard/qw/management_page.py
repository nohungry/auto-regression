"""
後台管理頁 Page Object — QW 站點（LM來財娛樂城）

QW 代理後台與 LU 同為 Vue admin 結構（側欄可見、子選單需展開、葉節點無 href、
`navigate_agent` 導航、user-account 下拉 logout），因此 re-export LU 實作以保留
QW 獨立命名空間。未來若 QW 後台出現差異，可改為 subclass 覆寫。
"""

from pages.dashboard.lu.management_page import ManagementPage

__all__ = ["ManagementPage"]
