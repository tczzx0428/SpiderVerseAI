from datetime import datetime, timedelta, timezone

CST = timezone(timedelta(hours=8))


def now_cst() -> datetime:
    """返回东八区当前时间（naive datetime，直接以 CST 本地时间存储）"""
    return datetime.now(CST).replace(tzinfo=None)
