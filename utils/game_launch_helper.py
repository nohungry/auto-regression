"""遊戲 launch 斷言輔助（新分頁型 LG/LU + 同分頁 iframe 型 RC/RD/RE 共用）。

新分頁型站點遊戲卡 → window.open 另開新分頁 → `<site>/launchLoading` →（後端簽發 token）→
轉址至**第三方 provider** 遊戲（LG=ugsdev gamelauncher / LU=royalgaming777 EnterGame2）。
遊戲為真錢、外部 provider、新分頁，**不做 spin**；
測試只驗「launch pipeline 成功」= 新分頁成功轉址離開本站，落到外部 provider host。
"""

import time
from urllib.parse import urlparse
from playwright.sync_api import Frame, Page, TimeoutError as PlaywrightTimeoutError


# Provider 端「啟動失敗」的明確錯誤詞（簡繁皆列）。只取「錯誤發生」語意的詞，
# 不用「客服 / 联系」等遊戲頁常見字（避免把正常遊戲誤判成錯誤）。
PROVIDER_ERROR_PHRASES = (
    "出现错误",
    "出現錯誤",
    "发生错误",
    "發生錯誤",
    "系统错误",
    "系統錯誤",
    "error has occurred",
    "something went wrong",
)


def provider_error(game_page: Page, timeout_ms: int = 3000) -> str | None:
    """回傳遊戲分頁 body 命中的 provider 錯誤詞（無錯誤回 None）。

    遊戲多渲染在 canvas/iframe，body inner_text 通常為空（非錯誤）；只有錯誤頁
    會以純文字呈現錯誤訊息，故「body 含明確錯誤詞」是穩定的失敗信號。
    """
    try:
        body = (game_page.locator("body").inner_text(timeout=timeout_ms) or "")
    except Exception:
        return None  # 抓不到 body（iframe-only 遊戲）視為無錯誤文字
    for phrase in PROVIDER_ERROR_PHRASES:
        if phrase in body:
            return phrase
    return None


def site_base_domain(site_url: str) -> str:
    """site_url 的可註冊網域（hostname 最後兩段），供「已離開本站」判定/斷言共用。

    domain 不硬編（D-014 精神：站點網域屬 .env 資訊），一律由 site_config.url 推導。
    """
    site_host = urlparse(site_url).hostname or ""
    return ".".join(site_host.split(".")[-2:])


def wait_for_provider_launch(
    game_page: Page, site_url: str, timeout_ms: int = 20000
) -> str:
    """等遊戲新分頁從 /launchLoading 轉址到外部第三方 provider host，回傳最終 URL。

    判定「離開本站」用 site_url 的可註冊網域（site_base_domain()）：hostname 不含該網域
    即視為已轉址到外部 provider，代表 launch pipeline（token 簽發 + 轉址）成功。

    逾時仍卡在本站 host（token 失敗 / launchLoading 未轉址）→ wait_for_url 拋
    TimeoutError，呼叫端視為 real FAIL，不掩蓋（被測站點 regression 訊號）。
    """
    base_domain = site_base_domain(site_url)

    def _is_external(url: str) -> bool:
        parsed = urlparse(url)
        host = parsed.hostname or ""
        if parsed.scheme not in ("http", "https") or not host:
            return False  # about:blank / 初始空白頁
        return base_domain not in host  # 仍在本站(含 launchLoading 中繼)→ False

    game_page.wait_for_url(_is_external, timeout=timeout_ms)
    return game_page.url


def launch_first_healthy_game(
    home, site_url: str, screenshotter=None, max_tries: int = 4, settle_ms: int = 6000
):
    """逐張嘗試啟動遊戲，回傳第一款「轉址到外部 provider 且非錯誤頁」的 (index, url, host)。

    為何要 retry：部分 provider 遊戲在 staging 啟動失敗（歷史案例：已退役的 KS
    前兩款 Pragmatic playGame.do 落到錯誤頁），故跳過壞掉的、取第一款乾淨載入的，
    使測試驗證的是「launch pipeline 確實能把玩家帶進可運作的遊戲」，而非僅僅轉址成功。

    `home` 須提供 open_slots_category() / launch_game(index)（LG/LU HomePage 皆有）。
    前 max_tries 款皆失敗（卡 launchLoading / 錯誤頁）→ raise AssertionError，
    視為疑似 provider regression（[[regression-notify-before-fix]]），不掩蓋。
    """
    attempts = []
    for idx in range(max_tries):
        if idx > 0:
            home.open_slots_category()  # 回分類頁再試下一款
        game_page = home.launch_game(idx)
        try:
            try:
                final_url = wait_for_provider_launch(game_page, site_url)
            except PlaywrightTimeoutError:
                attempts.append(f"#{idx}: 未轉址至外部 provider（卡 launchLoading）")
                continue
            game_page.wait_for_timeout(settle_ms)  # 等 provider 頁渲染（錯誤頁/loading）
            err = provider_error(game_page)
            if screenshotter:
                screenshotter.full_page(f"verify_遊戲{idx}_provider載入", page=game_page)
            if err is None:
                host = urlparse(final_url).hostname or ""
                return idx, final_url, host
            attempts.append(f"#{idx}({urlparse(final_url).hostname}): {err}")
        finally:
            game_page.close()
    raise AssertionError(
        f"slots 前 {max_tries} 款遊戲皆未能乾淨載入（疑似 provider regression）："
        + "; ".join(attempts)
    )


def get_game_frame(page: Page, timeout: int = 30000) -> Frame:
    """等待包含 canvas 的遊戲 iframe 出現（RC/RD/RE 信用版同分頁遊戲用）"""
    deadline = time.time() + timeout / 1000
    while time.time() < deadline:
        for frame in page.frames:
            if frame == page.main_frame:
                continue
            if frame.url and frame.url != "about:blank":
                try:
                    if frame.query_selector("canvas"):
                        return frame
                except Exception:
                    pass
        page.wait_for_timeout(500)
    raise RuntimeError(f"在 {timeout}ms 內找不到含 canvas 的遊戲 iframe")
