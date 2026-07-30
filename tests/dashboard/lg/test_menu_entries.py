"""
LG 後台側欄入口檢測（menu entry detection）— 站長層級

驗證「側欄有哪些入口 + 各入口對應的子入口」與預期 spec 完全一致（含順序）：
- 頂層入口：父項 a.memberSpan 的 route id（'' = 非路由項目）
- 子入口：父項底下葉節點的 href（站長側欄 href 為非同步掛載，
  sidebar_menu_tree 內含等待；收合狀態 DOM 即有全部節點，毋須展開）
選單增刪、順序、權限變動都會 fail —— 後台改版 / 權限異動的第一訊號。

斷言策略：結構性識別（route id / href），不綁文案（後台 locale 混雜：
英文 + 部分未翻譯 i18n key）；文案僅出現在 spec 註解供人類對照。
spec 來源：2026-07-30 實機 probe（headless chromium 直連 dev 站）。

⚠️ 帳號層級：dashboard_page = 站長（SITE_LG_DASHBOARD_USER，TOTP 2FA）。
   代理層級側欄葉節點**無 href**（Vue @click）→ 入口檢測另案處理（Phase 3），
   本檔不含代理層級。
"""

import pytest

from pages.dashboard.factory import get_dashboard_management_page_class

# 站長層級預期選單（頂層入口 route id → 子入口 href 清單，依側欄順序）
EXPECTED_MASTER_MENU = [
    ('', [  # Dashboard
        'Dashboard',
    ]),
    ('/member', [  # Member
        'Registration Review',
        'Member management',
        'Member deposit',
        'Member deposit(payment)',
        'Member withdraw',
        'BatchDispatch',
        'Member activity',
        'Member level V2',
        'MemberRebate V2',
        'Withdrawal rebate limit',
        'Kyc',
        'MemberTagsBatch',
        'BlacklistManagement',
    ]),
    ('/customService', [  # CustomService
        'CustomServiceMessageList',
        'GuestQuestioningList',
        'CustomServiceMessageTemplateList',
    ]),
    ('/agent', [  # Agent
        'Agent management',
        'Bank card inquiry',
        'Withdrew',
        'Rebate calculation V2',
        'Agent Data Overview',
    ]),
    ('/report', [  # Member Report
        'Member deposit',
        'Deposit report(payment)',
        'Withdrawal report',
        'Player Transfer record',
        'Point records',
        'Wallet records',
        'Credit records',
        'Amount adjustment',
        'Member Report Query',
    ]),
    ('/report-bet-count', [  # Betting report
        'Player report',
    ]),
    ('/statistical-report', [  # StatisticalReport
        'Data overviews',
        'BettingReportV2',
        'OperatingReport',
        'Game Stats',
        'AgentStatisticalAnalysis',
        'AgentDiscountStatistical',
        'Agent Activity Statistics',
        'MemberRanking',
        'MemberRetention',
        'Agent Data Analysis',
        'BettingReport',
        'Member Data Analysis',
    ]),
    ('/features', [  # Other settings
        'Company settings',
        'CompanySportSetting',
        'Bulletin',
        'PopupAnnouncement',
        'Group',
        'Bank',
        'CvsList',
        'Corporate bank',
        'Payment banking',
        'Payment method',
        'Payment method App',
        'Backend bank settings',
        'Crypto withdrawal settings',
        'Banner',
        'Activity setting V2',
        'Deposit and withdrawal settings',
        'Risk control',
        'Verification code',
        'Game maintenance',
        'Game emergency maintenance',
        'Member site mailbox',
        'Member site mailbox V2',
        'Tag management',
        'Store payment',
        'Virtual payment',
        'App version settings',
        'Add members in batches',
        'Block IP',
        'TG訊息設定',
    ]),
    ('/operationManagement', [  # Game management
        'Game type information',
        'Game information',
        'Game icon information',
        'Game type sort',
        'Platform Chips',
        'CasinoChipsRecord',
    ]),
    ('/blackList', [  # Blacklist
        'Blacklist rules',
        'Blacklist warnings',
        'App Blacklist',
    ]),
    ('/visit-control', [  # Background permissions
        'Role',
        'Account',
        'IP Whitelist',
        'RD account',
    ]),
    ('/report-various', [  # Background record
        'Member renewal record',
        'Administrator Login record',
        'Member login record',
        'Site mailbox record',
        'IP Whitelist Deletion Logs',
    ]),
    ('/SEO-Function', [  # Marketing function
        'SEO',
        'title.MemberAttribution',
        'title.VideoSetting',
    ]),
    ('/SEO-Blog-Function', [  # title.SEO-Blog-Function
        'title.SEO-blogCategory',
        'title.SEO-blog',
        'title.SEO-gameBlog',
        'title.SEO-blogActivity',
    ]),
    ('/mediaLibrary', [  # title.mediaLibrary
        'Chart gallery',
    ]),
    ('/accountingReport', [  # Financial statements
        'Registered member report',
        'Annual statistics',
    ]),
    ('/campaign', [  # Campaign
        'Luckydraw',
        'Invite Bonus',
        'Realtime Rebate',
        'Daily Bonus',
        'Redeem code',
        'Consecutive Check-in',
        'Task Wall List',
        'Coupon List',
    ]),
    ('/T9Gaming', [  # T9Gaming
        'T9 Table limit',
    ]),
]


@pytest.mark.p1
@pytest.mark.lg
@pytest.mark.dashboard
class TestMasterMenuEntries:
    """LG-DASH-MENU-001：站長側欄入口 + 子入口集合與 spec 精確一致。"""

    def test_master_menu_tree_matches_spec(self, dashboard_page, site_config):
        """dump 側欄選單樹（route id + 子入口 href）→ 與站長層級 spec 全等比對。"""
        Mgmt = get_dashboard_management_page_class(site_config.site_id)
        tree = Mgmt(dashboard_page).menu_tree()
        assert [p for p, _ in tree] == [p for p, _ in EXPECTED_MASTER_MENU], (
            f"站長頂層入口集合/順序變動：{[p for p, _ in tree]}"
        )
        assert tree == EXPECTED_MASTER_MENU, "站長子入口集合與 spec 不一致（見 diff）"


# 代理層級預期選單（權限子集；identity 規則同站長：頂層 route id + 子入口文字）
EXPECTED_AGENT_MENU = [
    ('/member', [  # Member
        'Member management',
    ]),
    ('/agent', [  # Agent
        'Agent management',
    ]),
    ('/report', [  # Member Report
        'Member deposit',
        'Deposit report(payment)',
        'Withdrawal report',
    ]),
    ('/report-bet-count', [  # Betting report
        'Player report',
    ]),
    ('/statistical-report', [  # StatisticalReport
        'BettingReportV2',
        'OperatingReport',
        'Game Stats',
        'AgentStatisticalAnalysis',
        'AgentDiscountStatistical',
        'Agent Activity Statistics',
        'Agent Data Analysis',
        'Member Data Analysis',
    ]),
]


@pytest.mark.p1
@pytest.mark.lg
@pytest.mark.dashboard
class TestAgentMenuEntries:
    """LG-DASH-MENU-002：代理側欄入口 + 子入口集合與 spec 精確一致。"""

    def test_agent_menu_tree_matches_spec(self, agent_dashboard_page, site_config):
        """dump 代理側欄選單樹 → 與代理層級 spec 全等比對。"""
        Mgmt = get_dashboard_management_page_class(site_config.site_id)
        tree = Mgmt(agent_dashboard_page).menu_tree()
        assert [p for p, _ in tree] == [p for p, _ in EXPECTED_AGENT_MENU], (
            f"代理頂層入口集合/順序變動：{[p for p, _ in tree]}"
        )
        assert tree == EXPECTED_AGENT_MENU, "代理子入口集合與 spec 不一致（見 diff）"
