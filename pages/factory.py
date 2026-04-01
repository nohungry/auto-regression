"""
Page Object Factory
根據 site_id 回傳對應站點的 Page Object class

使用 registry dict 映射，新增站點只需加一行。
未註冊的 site_id 會拋出 ValueError，不會靜默 fallback。
"""


def _import_class(module_path: str, class_name: str):
    """動態 import 指定模組中的 class"""
    import importlib
    module = importlib.import_module(module_path)
    return getattr(module, class_name)


# -----------------------------------------------
# Registry：site_id → (module_path, class_name)
# 新增站點只需在這裡加一行
# -----------------------------------------------
_LOGIN_PAGE_REGISTRY = {
    'drc': ('pages.drc.login_page', 'LoginPage'),
    'dlt': ('pages.dlt.login_page', 'LoginPage'),
}

_HOME_PAGE_REGISTRY = {
    'drc': ('pages.drc.home_page', 'HomePage'),
    'dlt': ('pages.dlt.home_page', 'HomePage'),
}


def _get_class(registry: dict, site_id: str, page_type: str):
    """從 registry 取得 class，未註冊則拋出明確錯誤"""
    if site_id not in registry:
        available = ', '.join(sorted(registry.keys()))
        raise ValueError(
            f"站點 '{site_id}' 的 {page_type} 未註冊。"
            f"可用站點：{available}。"
            f"請在 pages/factory.py 的 registry 中新增對應設定。"
        )
    module_path, class_name = registry[site_id]
    return _import_class(module_path, class_name)


def get_login_page_class(site_id: str):
    """根據 site_id 回傳對應的 LoginPage class"""
    return _get_class(_LOGIN_PAGE_REGISTRY, site_id, 'LoginPage')


def get_home_page_class(site_id: str):
    """根據 site_id 回傳對應的 HomePage class"""
    return _get_class(_HOME_PAGE_REGISTRY, site_id, 'HomePage')