"""
RF API 認證測試（金爺娛樂城，信用版）

API server 與 RC 共用同一套 t9platform API endpoint（見 .env SITE_RF_API_URL），
靠 header `companycode` / `domain` 區分站點。RF 的 companycode=drf，domain 見
.env SITE_RF_API_DOMAIN。

Login endpoint 與 response 結構與 RC 一致：
    POST /api/Member/memberLogin → {status: "Success", data: {token}}

Probe 結果（2026-06-17）：
- 正確帳密 → HTTP 200，status=Success，data.token 非空
- 錯誤密碼 → HTTP 400，status=Error，errorCode=InvalidOperate
- logout    → HTTP 200，status=Success

測試禁止 import pages/*（API 層獨立，純 requests，不啟動瀏覽器）。

執行方式：
    .venv/Scripts/pytest.exe tests/api/rf/test_auth.py -v
    .venv/Scripts/pytest.exe tests/api/rf/ -v
"""

import uuid
import pytest
import requests

LOGIN_PATH = "/api/Member/memberLogin"
LOGOUT_PATH = "/api/Member/memberLogout"


def _login(site_config, api_base_url, api_headers) -> str:
    """登入並回傳 token；用於需要獨立 session 的測試（例如 logout）"""
    resp = requests.post(
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
    assert resp.status_code == 200, f"登入失敗：{resp.text[:200]}"
    return resp.json()["data"]["token"]


@pytest.mark.p1
@pytest.mark.rf
@pytest.mark.api
class TestAuthAPI:

    def test_login_returns_token(self, site_config, api_base_url, api_headers):
        """TC-API-RF-001: 正確帳密應回傳 200 且 data.token 為非空字串"""
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
        """TC-API-RF-002: 錯誤密碼應回傳非 200 或 status != Success

        Probe 確認：錯誤密碼回 HTTP 400，status=Error，errorCode=InvalidOperate。
        """
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

    def test_logout_returns_success(self, site_config, api_base_url, api_headers):
        """TC-API-RF-003: 登出 API 回傳 Success

        注意：logout 回 Success 後同一 token 是否 server-side 失效未驗證
        （與 RC 行為一致，token 失效依賴 client 清除）。本測試只驗 logout
        endpoint 本身回 Success；若後端日後補 server-side 失效再加 assertion。
        """
        token = _login(site_config, api_base_url, api_headers)
        headers = {**api_headers, "authorization": token}

        logout_resp = requests.get(api_base_url + LOGOUT_PATH, headers=headers)
        assert logout_resp.status_code == 200, \
            f"logout 非 200：{logout_resp.status_code} {logout_resp.text[:200]}"
        body = logout_resp.json()
        assert body.get("status") == "Success", f"logout status 非 Success：{body}"
