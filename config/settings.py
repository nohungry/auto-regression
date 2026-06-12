"""
多站點設定管理
讀取 .env 檔案，根據 --site 參數回傳對應站點設定
"""

import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


@dataclass
class SiteConfig:
    site_id: str
    url: str
    username: str
    password: str
    dashboard_url: str = ""            # 站長入口（-admin）
    dashboard_agent_url: str = ""      # 代理入口（無 -admin）
    dashboard_user: str = ""
    dashboard_pass: str = ""
    dashboard_totp: str = ""
    dashboard_agent_user: str = ""
    dashboard_agent_pass: str = ""


def get_site_config(site_id: str = None) -> SiteConfig:
    """
    根據 site_id 取得站點設定
    若未指定 site_id，使用 .env 的 DEFAULT_SITE
    注意：env key 使用大寫 site_id（例如 SITE_RC_URL），回傳的 SiteConfig.site_id 則轉為小寫
    """
    if not site_id:
        site_id = os.getenv("DEFAULT_SITE", "wlj")

    site_id = site_id.upper()

    url = os.getenv(f"SITE_{site_id}_URL")
    username = os.getenv(f"SITE_{site_id}_USERNAME")
    password = os.getenv(f"SITE_{site_id}_PASSWORD")
    dashboard_url = os.getenv(f"SITE_{site_id}_DASHBOARD_URL", "")
    dashboard_agent_url = os.getenv(f"SITE_{site_id}_DASHBOARD_AGENT_URL", "")
    dashboard_user = os.getenv(f"SITE_{site_id}_DASHBOARD_USER", "")
    dashboard_pass = os.getenv(f"SITE_{site_id}_DASHBOARD_PASS", "")
    dashboard_totp = os.getenv(f"SITE_{site_id}_DASHBOARD_TOTP", "")
    dashboard_agent_user = os.getenv(f"SITE_{site_id}_DASHBOARD_AGENT_USER", "")
    dashboard_agent_pass = os.getenv(f"SITE_{site_id}_DASHBOARD_AGENT_PASS", "")

    if not url:
        raise ValueError(
            f"站點 '{site_id}' 設定不存在，請確認 .env 有設定 SITE_{site_id}_URL"
        )

    return SiteConfig(
        site_id=site_id.lower(),
        url=url,
        username=username,
        password=password,
        dashboard_url=dashboard_url,
        dashboard_agent_url=dashboard_agent_url,
        dashboard_user=dashboard_user,
        dashboard_pass=dashboard_pass,
        dashboard_totp=dashboard_totp,
        dashboard_agent_user=dashboard_agent_user,
        dashboard_agent_pass=dashboard_agent_pass,
    )
