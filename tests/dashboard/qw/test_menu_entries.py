"""
QW 後台側欄入口檢測（menu entry detection）— 站長層級

驗證「側欄有哪些入口 + 各入口對應的子入口」與預期 spec 完全一致（含順序）：
- 頂層入口：父項 a.memberSpan 的 route id（'' = 非路由項目）
- 子入口：父項底下葉節點的**顯示文字**（現金版葉節點無 href / id / class，
  文字是唯一穩定識別；helper = sidebar_menu_tree_texts，內含非同步掛載等待）
選單增刪、順序、權限變動都會 fail —— 後台改版 / 權限異動的第一訊號。

斷言策略：頂層用結構性 route id；子入口在現金版只能綁文字——後台為固定英文
＋部分未翻譯 i18n key（非多語系切換場景），故文案變動本身就是要回報的訊號。
spec 來源：2026-07-30 實機 probe（headless chromium 直連 dev 站）。

⚠️ lu / qw / lg 共用同一套 Vue admin 後台，三站站長 spec 逐字相同；
   後台選單改版時三個 test_menu_entries.py 要一起改（漏改的站會單獨紅）。
⚠️ 帳號層級：dashboard_page = 站長（SITE_QW_DASHBOARD_USER，TOTP 2FA）。
   本檔不含代理層級（待補）。2026-07-30 起代理 TwoFactorAuth/Verify 400 曾被歸因
   為「secret 遭伺服器端重綁」，**2026-08-28 實測證實 secret 正確**（站長與代理各自
   成功登入過，含使用者手動登入驗證）；400 真因是登入頻率 + TOTP 碼過期競態，
   已由 D-026（>=35s 登入節流 + 跨窗口重送一次）處理，非 secret 問題。
"""

import pytest

from pages.dashboard.factory import get_dashboard_management_page_class

# 站長層級預期選單（頂層入口 route id → 子入口顯示文字清單，依側欄順序）
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
@pytest.mark.qw
@pytest.mark.dashboard
class TestMasterMenuEntries:
    """QW-DASH-MENU-001：站長側欄入口 + 子入口集合與 spec 精確一致。"""

    def test_master_menu_tree_matches_spec(self, dashboard_page, site_config):
        """dump 側欄選單樹（route id + 子入口顯示文字）→ 與站長層級 spec 全等比對。"""
        Mgmt = get_dashboard_management_page_class(site_config.site_id)
        tree = Mgmt(dashboard_page).menu_tree()
        assert [p for p, _ in tree] == [p for p, _ in EXPECTED_MASTER_MENU], (
            f"站長頂層入口集合/順序變動：{[p for p, _ in tree]}"
        )
        assert tree == EXPECTED_MASTER_MENU, "站長子入口集合與 spec 不一致（見 diff）"
