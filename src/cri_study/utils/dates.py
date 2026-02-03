from datetime import datetime, timedelta


def to_jst(utc_dt: datetime) -> datetime:
    """UTC datetime を JST に変換 (UTC+9)"""
    return utc_dt + timedelta(hours=9)
