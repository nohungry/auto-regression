"""
DLT API 遊戲平台分類測試

    GET /api/Game/getGamePlatformCategoryList
    Headers: authorization=<token>
    Response: {data: [{category, bannerList, gamePlatformList: [{key, value, ...}]}], status: "Success"}
"""

import pytest
import requests

GAME_CATEGORY_PATH = "/api/Game/getGamePlatformCategoryList"


@pytest.mark.api
class TestGameCategoryAPI:

    def test_get_category_list_returns_structure(self, api_base_url, auth_headers):
        """TC-API-DLT-GAME-001: 已認證時取遊戲分類應回傳 status=Success 且 data 為非空 list"""
        resp = requests.get(api_base_url + GAME_CATEGORY_PATH, headers=auth_headers)

        assert resp.status_code == 200, \
            f"getGamePlatformCategoryList 非 200：{resp.status_code}，body：{resp.text[:300]}"

        body = resp.json()
        assert body.get("status") == "Success", f"status 非 Success：{body}"

        data = body.get("data")
        assert isinstance(data, list) and data, f"data 非非空 list：{data}"

        # 每個 category 應有 category 名稱與 gamePlatformList
        for item in data:
            assert "category" in item, f"category 欄位缺失：{item}"
            assert isinstance(item.get("gamePlatformList"), list), \
                f"gamePlatformList 非 list：{item}"

    def test_get_category_list_is_public(self, api_base_url, api_headers):
        """TC-API-DLT-GAME-002: 此 endpoint 為 public，無 token 應仍能取得遊戲分類

        遊戲型錄屬於進站前可瀏覽的資料（首頁即顯示），後端不要求 authorization。
        此測試鎖定此 public 行為；若後端改為需授權，此測試會 fail 提醒同步調整。
        """
        resp = requests.get(api_base_url + GAME_CATEGORY_PATH, headers=api_headers)
        assert resp.status_code == 200, f"public endpoint 非 200：{resp.status_code}"
        body = resp.json()
        assert body.get("status") == "Success", \
            f"public endpoint 不再 Success，後端可能已改為需授權：{body}"
        assert isinstance(body.get("data"), list) and body["data"], \
            f"public endpoint data 為空：{body}"
