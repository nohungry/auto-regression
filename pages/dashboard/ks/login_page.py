"""
後台登入頁面 Page Object — KS 站點（Super9娛樂城）

KS 代理後台與 LU 同為 Vue admin 結構（`#/member` 落點、5 項頂層選單、
登入鈕英文 Login、條件式 2FA），因此 re-export LU 實作以保留 KS 獨立命名空間。
未來若 KS 後台出現差異，可改為 subclass 覆寫。
"""

from pages.dashboard.lu.login_page import DashboardLoginPage

__all__ = ["DashboardLoginPage"]
