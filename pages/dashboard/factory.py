"""
Dashboard Page Object Factory
根據 site_id 回傳對應站點的後台 Page Object class

獨立於前台 factory（pages/factory.py），因為後台與前台是不同系統。
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
_DASHBOARD_LOGIN_REGISTRY = {
    'rc': ('pages.dashboard.rc.login_page', 'DashboardLoginPage'),
    'lt': ('pages.dashboard.lt.login_page', 'DashboardLoginPage'),
    're': ('pages.dashboard.re.login_page', 'DashboardLoginPage'),
    'rd': ('pages.dashboard.rd.login_page', 'DashboardLoginPage'),
    'lu': ('pages.dashboard.lu.login_page', 'DashboardLoginPage'),
    'lg': ('pages.dashboard.lg.login_page', 'DashboardLoginPage'),
    'ks': ('pages.dashboard.ks.login_page', 'DashboardLoginPage'),
}

_DASHBOARD_MANAGEMENT_REGISTRY = {
    'rc': ('pages.dashboard.rc.management_page', 'ManagementPage'),
    'lt': ('pages.dashboard.lt.management_page', 'ManagementPage'),
    're': ('pages.dashboard.re.management_page', 'ManagementPage'),
    'rd': ('pages.dashboard.rd.management_page', 'ManagementPage'),
    'lu': ('pages.dashboard.lu.management_page', 'ManagementPage'),
    'lg': ('pages.dashboard.lg.management_page', 'ManagementPage'),
    'ks': ('pages.dashboard.ks.management_page', 'ManagementPage'),
}


def _get_class(registry: dict, site_id: str, page_type: str):
    """從 registry 取得 class，未註冊則拋出明確錯誤"""
    if site_id not in registry:
        available = ', '.join(sorted(registry.keys()))
        raise ValueError(
            f"站點 '{site_id}' 的 Dashboard {page_type} 未註冊。"
            f"可用站點：{available}。"
            f"請在 pages/dashboard/factory.py 的 registry 中新增對應設定。"
        )
    module_path, class_name = registry[site_id]
    return _import_class(module_path, class_name)


def get_dashboard_login_page_class(site_id: str):
    """根據 site_id 回傳對應的 Dashboard LoginPage class"""
    return _get_class(_DASHBOARD_LOGIN_REGISTRY, site_id, 'LoginPage')


def get_dashboard_management_page_class(site_id: str):
    """根據 site_id 回傳對應的 Dashboard ManagementPage class"""
    return _get_class(_DASHBOARD_MANAGEMENT_REGISTRY, site_id, 'ManagementPage')
