"""
ks 站 API 測試專用 conftest

鏡像 tests/api/lt/conftest.py（含 origin/referer：後端 2026-05-29 起對保護端點
檢查 referer，缺 referer 回 PermissionDenied）。
"""

import os
import pytest
from dotenv import load_dotenv
from config.settings import get_site_config

load_dotenv()


@pytest.fixture(scope="session")
def site_config():
    return get_site_config("ks")


@pytest.fixture(scope="session")
def api_base_url():
    url = os.getenv("SITE_KS_API_URL")
    if not url:
        raise ValueError("請在 .env 設定 SITE_KS_API_URL")
    return url.rstrip("/")


@pytest.fixture(scope="session")
def api_headers(site_config):
    """API 請求必要 headers：companycode 識別站點，domain 對應站點識別碼，
    origin/referer 來自 site URL（後端對保護端點檢查 referer）。
    """
    domain = os.getenv("SITE_KS_API_DOMAIN")
    if not domain:
        raise ValueError("請在 .env 設定 SITE_KS_API_DOMAIN")
    companycode = os.getenv("SITE_KS_COMPANYCODE", "dks")
    site_origin = site_config.url.rstrip("/")
    return {
        "companycode": companycode,
        "domain": domain,
        "lang": "tw",
        "accept": "application/json",
        "content-type": "application/json",
        "origin": site_origin,
        "referer": site_origin + "/",
    }


@pytest.fixture(scope="session")
def auth_token(site_config, api_base_url, api_headers):
    """登入一次拿 token，session 共用"""
    import uuid
    import requests
    resp = requests.post(
        api_base_url + "/api/Member/memberLogin",
        json={
            "account": site_config.username,
            "password": site_config.password,
            "isMobile": False,
            "browser": "Chrome",
            "deviceId": uuid.uuid4().hex,
        },
        headers=api_headers,
    )
    assert resp.status_code == 200, f"登入失敗：{resp.status_code} {resp.text[:200]}"
    token = resp.json().get("data", {}).get("token", "")
    assert token, f"Token 為空：{resp.text[:200]}"
    return token


@pytest.fixture(scope="session")
def auth_headers(api_headers, auth_token):
    """已認證的 headers — authorization 為裸 token（無 Bearer 前綴）"""
    return {**api_headers, "authorization": auth_token}
