"""
DLT API 認證測試

登入 API 的職責是驗證帳密並回傳 token；
Cookie（LaiTsai / userLaiTsai）由前端 SPA 拿到 token 後自行寫入，
屬於前端行為，由 UI 層 test_login_success 間接覆蓋。

API endpoint 與 site domain 不同：
  Site:  https://dev-lt.t9platform.com      (SITE_DLT_URL)
  API:   https://dev-web-api.t9platform.com  (SITE_DLT_API_URL)

必要 headers：
  companycode — 站點識別碼（同 site_id）
  domain      — API 層站點識別 domain（SITE_DLT_API_DOMAIN，與 site URL 不同）

執行方式：
    .venv/bin/pytest tests/api/dlt/test_auth.py -v
    .venv/bin/pytest tests/api/ -m api -v
"""

import uuid
import pytest
import requests

LOGIN_PATH = "/api/Member/memberLogin"


@pytest.mark.api
class TestAuthAPI:

    def test_login_returns_token(self, site_config, api_base_url, api_headers):
        """TC-API-001 (API): 正確帳密應回傳 200 且 data.token 為非空字串"""
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
        """TC-API-002 (API): 錯誤密碼應回傳非 200 或 status != Success"""
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
