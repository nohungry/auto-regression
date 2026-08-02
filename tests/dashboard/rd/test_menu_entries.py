"""
RD 後台側欄入口檢測（menu entry detection）— 代理 + 總代/站長兩層級

驗證「側欄有哪些入口 + 各入口對應的子入口」與預期 spec 完全一致（含順序）：
- 頂層入口：父項 a.memberSpan 的 route id（'' = 非路由項目，如修改密碼/登出）
- 子入口：父項底下葉節點的 href（信用版 collapsed DOM 即存在，毋須展開）
選單增刪、順序、權限變動都會 fail —— 後台改版 / 權限異動的第一訊號。

斷言策略：結構性識別（route id / href），不綁文案（後台 locale 混雜）；
文案僅出現在 spec 註解供人類對照。
spec 來源：2026-07-30 實機 probe（headless chromium 直連 dev 站）。

⚠️ 帳號層級：dashboard_page = 代理（SITE_RD_DASHBOARD_AGENT_USER）、
   master_dashboard_page = 總代/站長（SITE_RD_DASHBOARD_USER）；權限不同 → spec 分開。
"""

import pytest

from pages.dashboard.factory import get_dashboard_management_page_class

# 代理層級預期選單（頂層入口 route id → 子入口 href 清單，依側欄順序）
EXPECTED_AGENT_MENU = [
    ('/management', []),  # 管理
    ('/report', [  # 報表
        '#/report/agentRevenueSplit',  # 代理拆帳報表
        '#/report/bet-report',  # 投注報表
        '#/report/quota-history',  # 會員額度歷史
        '#/report/agent-history',  # 代理額度歷史
        '#/report/giftRecord',  # 贈禮紀錄
        '#/report/operationRecord',  # 操作日誌
    ]),
    ('', ['#/userInfo/reset-password']),  # 修改密碼
    ('', []),  # 登出
]

# 總代/站長層級預期選單
EXPECTED_MASTER_MENU = [
    ('/dashboard', ['#/dashboard']),  # 儀表板
    ('/management', []),  # 管理
    ('/report', [  # 報表
        '#/report/agentRevenueSplit',  # 代理拆帳報表
        '#/report/bet-report',  # 投注報表
        '#/report/quota-history',  # 會員額度歷史
        '#/report/agent-history',  # 代理額度歷史
        '#/report/giftRecord',  # 贈禮紀錄
        '#/report/operationRecord',  # 操作日誌
    ]),
    ('/features', [  # 其它設定
        '#/features/announcement',  # 公告
        '#/features/banner',  # 橫幅
        '#/features/game-maintain',  # 例行遊戲維護
        '#/features/game-maintain-emergency',  # 遊戲緊急維護
        '#/features/discount-setupV2',  # 優惠設置 V2
        '#/features/memberPrivateMessage',  # 會員站內信
        '#/features/batchSend',  # 會員站內信 V2
        '#/features/gameVideoReplay',  # 高倍率回放
        '#/features/backendAnnouncement',  # 站內公告
        '#/features/liveStream',  # 直播設定
        '#/features/popupAnnouncement',  # 彈跳視窗公告
        '#/features/agentDomain',  # 指定域名設定
        '#/features/backendEntryImage',  # 後台入口圖
        '#/features/leaderboard',  # 排行榜
    ]),
    ('/operationManagement', [  # 遊戲管理
        '#/operationManagement/gamesCategoryInfo',  # 遊戲種類資訊
        '#/operationManagement/gameInfo',  # 遊戲資訊
        '#/operationManagement/gamesCategoryBanner',  # 遊戲圖示資訊
    ]),
    ('/visit-control', [  # 後臺權限
        '#/visit-control/custom-role',  # 角色
        '#/visit-control/office-user',  # 帳號
        '#/visit-control/rdAccount',  # 研發帳號
        '#/visit-control/whiteListIp',  # 後台IP白名單
    ]),
    ('/report-various', [  # 後臺紀錄
        '#/report-various/member-update-record',  # 會員更新紀錄
        '#/report-various/manager-record',  # 代理登入紀錄
        '#/report-various/member-login-record',  # 會員登入紀錄
        '#/report-various/whiteListIp-record',  # 後台IP刪除紀錄
    ]),
    ('', ['#/userInfo/reset-password']),  # 修改密碼
    ('', []),  # 登出
]


@pytest.mark.p1
@pytest.mark.rd
@pytest.mark.dashboard
class TestAgentMenuEntries:
    """RD-DASH-MENU-001：代理側欄入口 + 子入口集合與 spec 精確一致。"""

    def test_agent_menu_tree_matches_spec(self, dashboard_page, site_config):
        """dump 側欄選單樹（route id + 子入口 href）→ 與代理層級 spec 全等比對。"""
        Mgmt = get_dashboard_management_page_class(site_config.site_id)
        tree = Mgmt(dashboard_page).menu_tree()
        assert [p for p, _ in tree] == [p for p, _ in EXPECTED_AGENT_MENU], (
            f"代理頂層入口集合/順序變動：{[p for p, _ in tree]}"
        )
        assert tree == EXPECTED_AGENT_MENU, "代理子入口集合與 spec 不一致（見 diff）"


@pytest.mark.p1
@pytest.mark.rd
@pytest.mark.dashboard
class TestMasterMenuEntries:
    """RD-DASH-MENU-002：總代/站長側欄入口 + 子入口集合與 spec 精確一致。"""

    def test_master_menu_tree_matches_spec(self, master_dashboard_page, site_config):
        """dump 側欄選單樹 → 與總代/站長層級 spec 全等比對。"""
        Mgmt = get_dashboard_management_page_class(site_config.site_id)
        tree = Mgmt(master_dashboard_page).menu_tree()
        assert [p for p, _ in tree] == [p for p, _ in EXPECTED_MASTER_MENU], (
            f"站長頂層入口集合/順序變動：{[p for p, _ in tree]}"
        )
        assert tree == EXPECTED_MASTER_MENU, "站長子入口集合與 spec 不一致（見 diff）"
