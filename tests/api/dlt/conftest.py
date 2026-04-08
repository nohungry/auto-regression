"""
dlt 站 API 測試專用 conftest
"""

import os
import pytest
from dotenv import load_dotenv
from config.settings import get_site_config

load_dotenv()


@pytest.fixture(scope="session")
def site_config():
    return get_site_config("dlt")


@pytest.fixture(scope="session")
def api_base_url():
    url = os.getenv("SITE_DLT_API_URL")
    if not url:
        raise ValueError("請在 .env 設定 SITE_DLT_API_URL")
    return url.rstrip("/")


@pytest.fixture(scope="session")
def api_headers(site_config):
    """API 請求必要 headers：companycode 識別站點，domain 對應站點識別碼"""
    domain = os.getenv("SITE_DLT_API_DOMAIN")
    if not domain:
        raise ValueError("請在 .env 設定 SITE_DLT_API_DOMAIN")
    return {
        "companycode": site_config.site_id,
        "domain": domain,
        "lang": "tw",
        "accept": "application/json",
        "content-type": "application/json",
    }
