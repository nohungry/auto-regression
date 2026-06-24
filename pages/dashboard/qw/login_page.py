"""
後台登入頁面 Page Object — QW 站點（LM來財娛樂城）

QW 代理後台與 LU 同為 Vue admin 結構（`#/member` 落點、5 項頂層選單、
登入鈕英文 Login、條件式 2FA），因此 re-export LU 實作以保留 QW 獨立命名空間。

注意：QW 代理**需要 2FA**（與 LU/LG/KS 代理不同），TOTP secret 由
SITE_QW_DASHBOARD_AGENT_TOTP 提供；LU 的條件式 _fill_totp 會偵測 modal 並填碼。
未來若 QW 後台出現差異，可改為 subclass 覆寫。
"""

from pages.dashboard.lu.login_page import DashboardLoginPage

__all__ = ["DashboardLoginPage"]
