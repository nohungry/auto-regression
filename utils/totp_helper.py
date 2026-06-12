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
