"""
DLT API 會員資料測試

    GET /api/Member/getMemberInfoV3
    Headers: authorization=<token> (裸 token 無 Bearer)
    Response: {data: {id, account, nickname, ...}, status: "Success"}
"""

import pytest
import requests

MEMBER_INFO_PATH = "/api/Member/getMemberInfoV3"


@pytest.mark.api
class TestMemberAPI:

    def test_get_member_info_returns_account(self, site_config, api_base_url, auth_headers):
        """TC-API-DLT-MEM-001: 已認證時取會員資料應回傳 status=Success 且 account 相符"""
        resp = requests.get(api_base_url + MEMBER_INFO_PATH, headers=auth_headers)

        assert resp.status_code == 200, \
            f"getMemberInfoV3 回傳非 200：{resp.status_code}，body：{resp.text[:300]}"

        body = resp.json()
        assert body.get("status") == "Success", f"status 非 Success：{body}"

        data = body.get("data") or {}
        assert data.get("account") == site_config.username, \
            f"account 不符，預期 {site_config.username}，實際 {data.get('account')}"
        # 關鍵欄位存在
        for key in ("id", "account", "nickname", "avatar"):
            assert key in data, f"回傳缺少欄位 {key}：{data}"

    def test_get_member_info_without_token_fails(self, api_base_url, api_headers):
        """TC-API-DLT-MEM-002: 無 authorization 時應無法取得會員資料"""
        resp = requests.get(api_base_url + MEMBER_INFO_PATH, headers=api_headers)
        body = resp.json() if resp.headers.get("content-type", "").startswith("application/json") else {}
        assert resp.status_code != 200 or body.get("status") != "Success", \
            f"無 token 不應成功，status={resp.status_code}，body：{resp.text[:200]}"

    def test_get_member_info_with_invalid_token_fails(self, api_base_url, api_headers):
        """TC-API-DLT-MEM-003: 無效 token 時應無法取得會員資料"""
        headers = {**api_headers, "authorization": "00000000-0000-0000-0000-000000000000"}
        resp = requests.get(api_base_url + MEMBER_INFO_PATH, headers=headers)
        body = resp.json() if resp.headers.get("content-type", "").startswith("application/json") else {}
        assert resp.status_code != 200 or body.get("status") != "Success", \
            f"無效 token 不應成功，status={resp.status_code}，body：{resp.text[:200]}"
