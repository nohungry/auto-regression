"""
drc 站 API 測試專用 conftest
"""

import pytest
from config.settings import get_site_config


@pytest.fixture(scope="session")
def site_config():
    return get_site_config("drc")
