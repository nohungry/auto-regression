"""
DLT API 投注紀錄測試

    POST /api/Report/getMemberBetRecordList_V2
    Headers: authorization=<token>
    Payload: {gamePlatform, gamesCategory, start, end}
    Response: {data: {list: [], pageCount: int, totalCount: int}, status: "Success"}
"""

from datetime import datetime
import pytest
import requests

from tests.api.dlt.test_auth import _login

BET_RECORD_PATH = "/api/Report/getMemberBetRecordList_V2"


def _today_range() -> dict:
    today = datetime.now().strftime("%Y-%m-%d")
    return {
        "gamePlatform": 0,
        "gamesCategory": 0,
        "start": f"{today}T00:00:00",
        "end": f"{today}T23:59:00",
    }


@pytest.mark.api
class TestBetRecordAPI:

    @pytest.mark.xfail(
        reason="後端對此 endpoint 有額外 side-channel 檢查（疑似 IP 白名單/TLS 指紋/"
               "session cookie 綁定）。同一個 token 呼叫 getBalance 200 但此 API 500 "
               "InternalError；完整比照瀏覽器 headers（companycode/domain/lang/origin/"
               "referer/subagentcode）依然 500。非 client 端可修復，後端修好後此測試"
               "會自動轉為 XPASS 提醒。",
        strict=False,
    )
    def test_get_bet_record_returns_structure(self, site_config, api_base_url, api_headers):
        """TC-API-DLT-BET-001: 已認證取當日投注紀錄應回傳 list/pageCount/totalCount 結構"""
        token = _login(site_config, api_base_url, api_headers)
        headers = {**api_headers, "authorization": token}
        resp = requests.post(api_base_url + BET_RECORD_PATH, json=_today_range(), headers=headers)

        assert resp.status_code == 200, \
            f"getMemberBetRecordList_V2 非 200：{resp.status_code}，body：{resp.text[:300]}"

        body = resp.json()
        assert body.get("status") == "Success", f"status 非 Success：{body}"

        data = body.get("data") or {}
        assert isinstance(data.get("list"), list), f"data.list 非 list：{data}"
        assert isinstance(data.get("pageCount"), int), f"data.pageCount 非 int：{data}"
        assert isinstance(data.get("totalCount"), int), f"data.totalCount 非 int：{data}"
        assert data["totalCount"] >= 0, f"totalCount 為負值：{data}"

    def test_get_bet_record_without_token_fails(self, api_base_url, api_headers):
        """TC-API-DLT-BET-002: 無 authorization 時應無法取得投注紀錄"""
        resp = requests.post(api_base_url + BET_RECORD_PATH, json=_today_range(), headers=api_headers)
        body = resp.json() if resp.headers.get("content-type", "").startswith("application/json") else {}
        assert resp.status_code != 200 or body.get("status") != "Success", \
            f"無 token 不應成功，status={resp.status_code}，body：{resp.text[:200]}"

    def test_get_bet_record_with_invalid_token_fails(self, api_base_url, api_headers):
        """TC-API-DLT-BET-003: 無效 token 時應無法取得投注紀錄"""
        headers = {**api_headers, "authorization": "00000000-0000-0000-0000-000000000000"}
        resp = requests.post(api_base_url + BET_RECORD_PATH, json=_today_range(), headers=headers)
        body = resp.json() if resp.headers.get("content-type", "").startswith("application/json") else {}
        assert resp.status_code != 200 or body.get("status") != "Success", \
            f"無效 token 不應成功，status={resp.status_code}，body：{resp.text[:200]}"
