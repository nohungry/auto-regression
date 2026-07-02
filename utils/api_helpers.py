"""
API 測試共用邏輯（跨 9 站的 env 推導 / headers / 登入拿 token）。

這裡放的是**純函式**，不是 fixture：各站 `tests/api/<id>/conftest.py` 仍各自
定義 session-scoped fixture（`site_config` / `api_base_url` / `api_headers` /
`auth_token` / `auth_headers`），fixture body 只呼叫本檔函式。

為何 fixture 仍要 per-site 而非抽到共用父 conftest：session-scoped fixture 若定義
在共用父 conftest，pytest 對該單一 FixtureDef 整個 session 只快取一次 → 多站在
同一 pytest session 跑時，第一站算出的 token 會被其它站重用（跨站污染）。各站各自
定義 fixture 才有獨立 session 快取。故「邏輯單一來源 + fixture per-site」兩者兼顧。

站別差異全由 `site_config.site_id` 推導：env 前綴 `SITE_<ID>_*`、companycode 預設
`"d"+id`。後端 2026-05-29 起對保護端點檢查 referer，故 headers 帶 origin/referer。
"""

import os
import uuid

import requests


def _env_prefix(site_config) -> str:
    """站別 env 前綴，如 rc → 'SITE_RC'。"""
    return f"SITE_{site_config.site_id.upper()}"


def api_base_url_for(site_config) -> str:
    key = f"{_env_prefix(site_config)}_API_URL"
    url = os.getenv(key)
    if not url:
        raise ValueError(f"請在 .env 設定 {key}")
    return url.rstrip("/")


def api_headers_for(site_config) -> dict:
    """API 請求必要 headers：companycode 識別站點，domain 對應站點識別碼，
    origin/referer 來自 site URL（後端對保護端點檢查 referer）。
    """
    prefix = _env_prefix(site_config)
    domain = os.getenv(f"{prefix}_API_DOMAIN")
    if not domain:
        raise ValueError(f"請在 .env 設定 {prefix}_API_DOMAIN")
    companycode = os.getenv(f"{prefix}_COMPANYCODE", f"d{site_config.site_id}")
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


def login_for_token(site_config, api_base_url: str, api_headers: dict) -> str:
    """POST memberLogin 拿裸 token（無 Bearer 前綴）；登入或 token 為空即 assert 失敗。"""
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
