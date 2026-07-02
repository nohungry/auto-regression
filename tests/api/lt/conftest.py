"""lt 站 API 測試 conftest：fixture 保持 per-site（獨立 session 快取），
共用邏輯見 utils/api_helpers.py（詳為何 fixture 不抽父層見該檔 docstring）。"""

import pytest
from config.settings import get_site_config
from utils.api_helpers import api_base_url_for, api_headers_for, login_for_token


@pytest.fixture(scope="session")
def site_config():
    return get_site_config("lt")


@pytest.fixture(scope="session")
def api_base_url(site_config):
    return api_base_url_for(site_config)


@pytest.fixture(scope="session")
def api_headers(site_config):
    return api_headers_for(site_config)


@pytest.fixture(scope="session")
def auth_token(site_config, api_base_url, api_headers):
    return login_for_token(site_config, api_base_url, api_headers)


@pytest.fixture(scope="session")
def auth_headers(api_headers, auth_token):
    return {**api_headers, "authorization": auth_token}
