"""
RF API 遊戲平台分類測試（金爺娛樂城，信用版）

    GET /api/Game/getGamePlatformCategoryList
    Headers: companycode=drf, domain=dev-rf.t9platform.com（無需 authorization）
    Response: {data: [{category, bannerList, gamePlatformList: [...]}, ...], status: "Success"}

Probe 結果（2026-06-17）：
- 有效 token → HTTP 200，status=Success，data 為 8 個分類的 list
- 無 token   → HTTP 200，status=Success（同樣 8 個分類，此端點為 public）
- 每個分類含 category、bannerList、gamePlatformList 欄位

測試禁止 import pages/*（API 層獨立，純 requests，不啟動瀏覽器）。
"""

import pytest
import requests

GAME_CATEGORY_PATH = "/api/Game/getGamePlatformCategoryList"


@pytest.mark.p1
@pytest.mark.rf
@pytest.mark.api
@pytest.mark.game
class TestGameCategoryAPI:

    def test_get_category_list_returns_structure(self, api_base_url, auth_headers):
        """TC-API-RF-GAME-001: 已認證時取遊戲分類應回傳 status=Success 且 data 為非空 list"""
        resp = requests.get(api_base_url + GAME_CATEGORY_PATH, headers=auth_headers)

        assert resp.status_code == 200, \
            f"getGamePlatformCategoryList 非 200：{resp.status_code}，body：{resp.text[:300]}"

        body = resp.json()
        assert body.get("status") == "Success", f"status 非 Success：{body}"

        data = body.get("data")
        assert isinstance(data, list) and data, f"data 非非空 list：{data}"

        for item in data:
            assert "category" in item, f"category 欄位缺失：{item}"
            assert isinstance(item.get("gamePlatformList"), list), \
                f"gamePlatformList 非 list：{item}"

    def test_get_category_list_is_public(self, api_base_url, api_headers):
        """TC-API-RF-GAME-002: 此 endpoint 為 public，無 token 應仍能取得遊戲分類

        Probe 確認：無 token 與有 token 均回傳相同 8 個分類，此端點不需授權（首頁進站前即顯示）。
        若後端改為需授權，此測試會 fail 提醒同步調整。
        """
        resp = requests.get(api_base_url + GAME_CATEGORY_PATH, headers=api_headers)
        assert resp.status_code == 200, f"public endpoint 非 200：{resp.status_code}"
        body = resp.json()
        assert body.get("status") == "Success", \
            f"public endpoint 不再 Success，後端可能已改為需授權：{body}"
        assert isinstance(body.get("data"), list) and body["data"], \
            f"public endpoint data 為空：{body}"
