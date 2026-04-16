"""
rc 站 API 測試專用 conftest
"""

import os
import pytest
from dotenv import load_dotenv
from config.settings import get_site_config

load_dotenv()


@pytest.fixture(scope="session")
def site_config():
    return get_site_config("rc")


@pytest.fixture(scope="session")
def api_base_url():
    url = os.getenv("SITE_RC_API_URL")
    if not url:
        raise ValueError("請在 .env 設定 SITE_RC_API_URL")
    return url.rstrip("/")


@pytest.fixture(scope="session")
def api_headers(site_config):
    """API 請求必要 headers：companycode 識別站點，domain 對應站點識別碼"""
    domain = os.getenv("SITE_RC_API_DOMAIN")
    if not domain:
        raise ValueError("請在 .env 設定 SITE_RC_API_DOMAIN")
    companycode = os.getenv("SITE_RC_COMPANYCODE", "drc")
    return {
        "companycode": companycode,
        "domain": domain,
        "lang": "tw",
        "accept": "application/json",
        "content-type": "application/json",
    }
