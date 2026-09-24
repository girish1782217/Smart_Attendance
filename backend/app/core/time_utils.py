from datetime import datetime, timezone


def utc_now() -> datetime:
    """Naive UTC now — kept naive so SQLite/Postgres DateTime columns compare consistently."""
    return datetime.now(timezone.utc).replace(tzinfo=None)
