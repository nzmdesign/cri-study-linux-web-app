from datetime import datetime, timedelta

def to_jst(utc_dt: datetime | None) -> datetime | None:
    """UTC datetime を JST に変換 (UTC+9)"""
    if utc_dt is None:
        return None
    return utc_dt + timedelta(hours=9)
