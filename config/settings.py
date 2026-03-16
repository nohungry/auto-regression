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


def get_site_config(site_id: str = None) -> SiteConfig:
    """
    根據 site_id 取得站點設定
    若未指定 site_id，使用 .env 的 DEFAULT_SITE
    """
    if not site_id:
        site_id = os.getenv("DEFAULT_SITE", "wlj")

    site_id = site_id.upper()

    url = os.getenv(f"SITE_{site_id}_URL")
    username = os.getenv(f"SITE_{site_id}_USERNAME")
    password = os.getenv(f"SITE_{site_id}_PASSWORD")

    if not url:
        raise ValueError(
            f"站點 '{site_id}' 設定不存在，請確認 .env 有設定 SITE_{site_id}_URL"
        )

    return SiteConfig(
        site_id=site_id.lower(),
        url=url,
        username=username,
        password=password,
    )
