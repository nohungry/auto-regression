"""
RF API 錢包測試（金爺娛樂城，信用版）

    GET /api/MemberWallet/getBalance
    Headers: authorization=<token>（裸 token，無 Bearer 前綴）
    Response: {data: {balance: float}, status: "Success"}

Probe 結果（2026-06-17）：
- 有效 token → HTTP 200，status=Success，data.balance=10000.0（float）
- 無 token   → HTTP 401 或 status != Success（依後端保護機制）
- 無效 token → HTTP 401 或 status != Success

斷言策略：
- balance 只驗型別（int/float）與非負，不寫死特定數值（信用版餘額為可調整的固定額度）。

測試禁止 import pages/*（API 層獨立，純 requests，不啟動瀏覽器）。
"""

import pytest
import requests

BALANCE_PATH = "/api/MemberWallet/getBalance"


@pytest.mark.p1
@pytest.mark.rf
@pytest.mark.api
@pytest.mark.wallet
class TestWalletAPI:

    def test_get_balance_returns_number(self, api_base_url, auth_headers):
        """TC-API-RF-WAL-001: 已認證時取餘額應回傳 status=Success 且 balance 為數值

        只驗型別（int/float）與非負，不寫死特定數值（信用版餘額為可調整的固定額度）。
        """
        resp = requests.get(api_base_url + BALANCE_PATH, headers=auth_headers)

        assert resp.status_code == 200, \
            f"getBalance 回傳非 200：{resp.status_code}，body：{resp.text[:300]}"

        body = resp.json()
        assert body.get("status") == "Success", f"status 非 Success：{body}"

        data = body.get("data") or {}
        balance = data.get("balance")
        assert isinstance(balance, (int, float)), \
            f"balance 非數值，實際型別 {type(balance).__name__}：{data}"
        assert balance >= 0, f"balance 為負值：{balance}"

    def test_get_balance_without_token_fails(self, api_base_url, api_headers):
        """TC-API-RF-WAL-002: 無 authorization 時應無法取得餘額"""
        resp = requests.get(api_base_url + BALANCE_PATH, headers=api_headers)
        body = resp.json() if resp.headers.get("content-type", "").startswith("application/json") else {}
        assert resp.status_code != 200 or body.get("status") != "Success", \
            f"無 token 不應成功，status={resp.status_code}，body：{resp.text[:200]}"

    def test_get_balance_with_invalid_token_fails(self, api_base_url, api_headers):
        """TC-API-RF-WAL-003: 無效 token 時應無法取得餘額"""
        headers = {**api_headers, "authorization": "00000000-0000-0000-0000-000000000000"}
        resp = requests.get(api_base_url + BALANCE_PATH, headers=headers)
        body = resp.json() if resp.headers.get("content-type", "").startswith("application/json") else {}
        assert resp.status_code != 200 or body.get("status") != "Success", \
            f"無效 token 不應成功，status={resp.status_code}，body：{resp.text[:200]}"
