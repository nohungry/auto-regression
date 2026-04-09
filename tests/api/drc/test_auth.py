"""
DRC API 認證測試

API server 與 DLT 共用 dev-web-api.t9platform.com，靠 header `companycode` / `domain` 區分站點。
DRC 的 companycode=drc，domain=dev-drc.t9platform-ph.com。

Login endpoint 與 response 結構與 DLT 一致：
    POST /api/Member/memberLogin → {status: "Success", data: {token}}

執行方式：
    .venv/bin/pytest tests/api/drc/test_auth.py -v
    .venv/bin/pytest tests/api/ -m api -v
"""

import uuid
import pytest
import requests

LOGIN_PATH = "/api/Member/memberLogin"


@pytest.mark.api
class TestAuthAPI:

    def test_login_returns_token(self, site_config, api_base_url, api_headers):
        """TC-API-DRC-001: 正確帳密應回傳 200 且 data.token 為非空字串"""
        session = requests.Session()
        resp = session.post(
            api_base_url + LOGIN_PATH,
            json={
                "account": site_config.username,
                "password": site_config.password,
                "isMobile": False,
                "browser": "Chrome",
                "deviceId": uuid.uuid4().hex,
            },
            headers=api_headers,
        )

        assert resp.status_code == 200, \
            f"Login API 回傳非預期狀態碼：{resp.status_code}，body：{resp.text[:300]}"

        body = resp.json()
        assert body.get("status") == "Success", \
            f"回傳 status 非 Success：{body}"
        token = body.get("data", {}).get("token", "")
        assert token, f"data.token 為空，body：{body}"

    def test_login_wrong_password_returns_error(self, site_config, api_base_url, api_headers):
        """TC-API-DRC-002: 錯誤密碼應回傳非 200 或 status != Success"""
        session = requests.Session()
        resp = session.post(
            api_base_url + LOGIN_PATH,
            json={
                "account": site_config.username,
                "password": "wrong_password_123",
                "isMobile": False,
                "browser": "Chrome",
                "deviceId": uuid.uuid4().hex,
            },
            headers=api_headers,
        )

        body = resp.json()
        assert resp.status_code != 200 or body.get("status") != "Success", \
            f"錯誤密碼不應登入成功，body：{body}"
