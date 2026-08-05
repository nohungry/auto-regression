"""
go_home fixture 的共用「回首頁 + 清彈窗」邏輯，供各站 tests/<id>/conftest.py 呼叫。

各站 go_home 是 function-scoped fixture，仍在各站 conftest 各自定義（body 只呼叫
這裡的函式）。兩型：

- **dialog-dismisser 型**（rc/re/rd，共用平台前台）：goto → networkidle →
  等 Loading 消失 → dismiss server error / announcement（rd 另清蓋板 dialog-mask）。
- **home-popup 型**（qw/lg/lu/rf，Nuxt/Vue）：goto 後委由該站
  HomePage.dismiss_any_popups() 清彈窗（各站 popup selector 差異封裝在該站 POM）。
"""

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

from pages.factory import get_home_page_class
from utils.dialog_helper import (
    dismiss_server_error_if_present,
    dismiss_announcement_popup_if_present,
    dismiss_dialog_mask_if_present,
)


def reset_home_with_dismissers(pg, url, dismiss_mask: bool = False) -> None:
    """rc/re/rd 型：networkidle + 等 Loading 消失 + server error / announcement 彈窗
    （dismiss_mask=True 時另清 rd 專屬蓋板 .dialog-mask，會攔截 navbar 點擊）。
    """
    pg.goto(url)
    pg.wait_for_load_state("networkidle")
    try:
        pg.locator('img[alt="Loading"]').wait_for(state="hidden", timeout=5000)
    except PlaywrightTimeoutError:
        pass
    dismiss_server_error_if_present(pg)
    dismiss_announcement_popup_if_present(pg)
    if dismiss_mask:
        dismiss_dialog_mask_if_present(pg)


def reset_home_with_home_popups(
    pg, url, site_id: str, wait_until: str = "domcontentloaded", timeout: int = 60000
) -> None:
    """qw/lg/lu/rf 型：goto 後委由該站 HomePage.dismiss_any_popups() 清彈窗。

    lg/lu/rf 用預設（domcontentloaded + 60s）；qw 傳 wait_until='networkidle'。
    """
    pg.goto(url, wait_until=wait_until, timeout=timeout)
    home = get_home_page_class(site_id)(pg)
    home.dismiss_any_popups()
