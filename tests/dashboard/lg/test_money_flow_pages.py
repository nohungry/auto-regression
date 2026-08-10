"""
LG 後台金流頁入口檢測（會員存提審核頁 + 金流報表頁）— 站長層級

驗證「存款/提款相關的 9 個後台頁」皆可達，且各頁表格欄位與 spec 完全一致（含順序）：
- 會員區：Member deposit / Member deposit(payment) / Member withdraw（存提單審核頁）
- 報表區：Member deposit / Deposit report(payment) / Withdrawal report /
          Point records / Wallet records / Amount adjustment

read-only：只導航 + 讀 thead，不查詢、不改任何金流資料。

斷言策略：route hash 為結構性識別（不隨文案變）；欄位用**顯示文字**全等比對——
後台為固定英文顯示（非多語系切換場景），欄位增刪／改名／換順序都是後台改版或
權限異動要回報的第一訊號。現金版側欄葉節點無 href（Vue @click），故用 route 直接
goto（同 goto_member_management 慣例），不受側欄收合狀態影響。

spec 來源：2026-08-10 實機 probe（headless 不可行，走 CDP）。
⚠️ lu / qw / lg 共用同一套 Vue admin 後台，三站 route 與欄位**逐字全等**（已實測比對）；
   後台改版時三個 test_money_flow_pages.py 要一起改（漏改的站會單獨紅）。
⚠️ 帳號層級：dashboard_page = 站長（SITE_LG_DASHBOARD_USER，TOTP 2FA）。
   代理層級可見的報表較少（LG 代理僅 3 項），本檔不含代理層級。
"""

import pytest

from pages.dashboard.factory import get_dashboard_management_page_class

# 站長層級預期金流頁（route hash → 表格欄位顯示文字清單，依欄位順序）
MONEY_FLOW_PAGES = [
    # 側欄 /member > Member deposit
    (
        '/member/member-deposit',
        [
            'Member',
            'Tag',
            'Member bake name',
            'Member bank name',
            'Member bank account',
            'Transfer info',
            'Submit date',
            'Beneficiary bank info',
            'Bank deposit',
            'Status',
            'Remark',
            'Administrator',
            'Processing date',
        ],
    ),
    # 側欄 /member > Member deposit(payment)
    (
        '/member/member-deposit-store',
        [
            'Status',
            'Pick up time',
            'Payment Details',
            'Member',
            'Tag',
            'Amount Info.',
            'Time of built',
            'Processing date',
            'Administrator',
            'Payment information',
            'Remark',
        ],
    ),
    # 側欄 /member > Member withdraw
    (
        '/member/member-withdraw',
        [
            'Status',
            'Agent',
            'Member',
            'Tag',
            'Amount Info.',
            'Withdrawal Details',
            'Bank Info',
            'Submit date',
            'Processing date',
            'Payment merchant',
            'Payment order number',
            'Remark',
            'Operator',
        ],
    ),
    # 側欄 /report > Member deposit
    (
        '/report/member-deposit',
        [
            'Submit date',
            'Member',
            'Tag',
            'Member bank',
            'Amount',
            'Bank deposit',
            'Status',
            'Remark',
            'Administrator',
            'Processing date',
        ],
    ),
    # 側欄 /report > Deposit report(payment)
    (
        '/report/member-deposit-payment-report',
        [
            'Deposit method',
            'Status',
            'Member',
            'Tag',
            'Date created',
            'Pick up time',
            'Order Number',
            'Virtual account number/Store code/Credit card number',
            'Cash flow merchant',
            'Original amount',
            'Handling fee',
            'Actual receipt amount',
            'Payment information',
            'Remark',
            'Administrator',
            'Processing date',
        ],
    ),
    # 側欄 /report > Withdrawal report
    (
        '/report/member-withdrawal-report',
        [
            'Submit date',
            'Member',
            'Tag',
            'Bank',
            'Account name',
            'Account number',
            'Payment order number',
            'Amount',
            'Currency',
            'Exchange rate',
            'A/R(Crypto)',
            'Status',
            'Remark',
            'Payment merchant',
            'Administrator',
            'Processing date',
        ],
    ),
    # 側欄 /report > Point records
    (
        '/report/memberPointRecord',
        [
            'Sort',
            'Agent',
            'Member',
            'Nick Name',
            'Point Category',
            'Earn Point',
            'Starting Point',
            'Ending Point',
            'Remark',
            'Operator',
            'Operating time',
        ],
    ),
    # 側欄 /report > Wallet records
    (
        '/report/wallet-history',
        [
            'Operate',
            'Member',
            'Date',
            'Starting balance',
            '>Amount',
            'Ending balance',
            'Remark',
        ],
    ),
    # 側欄 /report > Amount adjustment
    (
        '/report/balance-adjustment-report',
        [
            'Member',
            'Tag',
            'Adjustment type',
            'Starting balance',
            'Amount',
            'Ending balance',
            'Remark',
            'Administrator',
            'Processing date',
        ],
    ),
]


@pytest.mark.p1
@pytest.mark.lg
@pytest.mark.dashboard
@pytest.mark.wallet
class TestMoneyFlowPages:
    """LG-DASH-MONEY-001：金流頁可達 + 表格欄位與 spec 精確一致。"""

    @pytest.mark.parametrize(
        "route,expected_headers", MONEY_FLOW_PAGES, ids=[r for r, _ in MONEY_FLOW_PAGES]
    )
    def test_money_flow_page_headers(self, dashboard_page, site_config, route, expected_headers):
        """導航至金流頁 → dump thead 欄位 → 與 spec 全等比對。"""
        Mgmt = get_dashboard_management_page_class(site_config.site_id)
        mgmt = Mgmt(dashboard_page)

        mgmt.goto_money_flow_page(site_config.dashboard_url, route)
        assert route in dashboard_page.url, (
            f"導航後 URL 未含 {route}：{dashboard_page.url}"
        )

        headers = mgmt.table_headers()
        assert headers == expected_headers, (
            f"{route} 表格欄位與 spec 不一致\n"
            f"  實得：{headers}\n"
            f"  預期：{expected_headers}"
        )
