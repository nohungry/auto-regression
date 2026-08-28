"""
TOTP（Google Authenticator）兩步驟驗證碼 Helper

用於後台需 2FA 的站台（首站：LU Super... Dlgbet 後台）。
secret 為 base32 金鑰，存於 .env `SITE_<ID>_DASHBOARD_TOTP`，載入到
`site_config.dashboard_totp`，由 pyotp 即時產生 6 碼。
"""

import time

import pyotp


def get_totp_code(secret: str, min_remaining: int = 5) -> str:
    """
    依 base32 secret 產生當前 TOTP 6 碼。

    TOTP 每 30 秒輪替一次；若當前窗口剩餘秒數 < min_remaining，
    先等到下一個窗口再產碼，避免「產碼 → 填入 → 送出」途中碼剛好過期
    導致後端驗證失敗的 race。

    Args:
        secret: base32 TOTP 金鑰
        min_remaining: 容許的最小剩餘秒數，低於此值則等下一窗口

    Returns:
        6 位數字字串
    """
    if not secret:
        raise ValueError("TOTP secret 為空，請確認 .env 的 SITE_<ID>_DASHBOARD_TOTP 已設定")

    totp = pyotp.TOTP(secret)
    remaining = totp.interval - (time.time() % totp.interval)
    if remaining < min_remaining:
        # 非 UI 等待：對齊 TOTP 30s 旋轉窗口，避免提交瞬間驗證碼失效
        time.sleep(remaining + 1)
    return totp.now()


def get_next_window_totp_code(secret: str) -> str:
    """等到**下一個** TOTP 窗口再產碼，保證與當前窗口的碼不同。

    重送專用：2FA Verify 被後端拒絕（400）後若拿同一窗口的碼重送，等同同碼
    重放，後端必然再拒；必須跨過 30s 旋轉窗口取得全新的碼才有意義。
    與 `get_totp_code` 的差別：後者只在「快過期」時才等窗口（樂觀取當前碼），
    本函式**無條件**等到窗口翻轉。

    Args:
        secret: base32 TOTP 金鑰

    Returns:
        6 位數字字串（保證來自新的 30s 窗口）
    """
    if not secret:
        raise ValueError("TOTP secret 為空，請確認 .env 的 SITE_<ID>_DASHBOARD_TOTP 已設定")

    totp = pyotp.TOTP(secret)
    remaining = totp.interval - (time.time() % totp.interval)
    # 非 UI 等待：對齊 TOTP 30s 旋轉窗口（D-006 核可例外，同上方 get_totp_code 先例）。
    # 窗口翻轉是純 wall-clock 條件，沒有任何 UI / API 信號可 poll。+1s 為跨越邊界的裕度。
    time.sleep(remaining + 1)
    return totp.now()
