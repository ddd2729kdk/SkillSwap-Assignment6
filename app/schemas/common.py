from datetime import datetime, timezone


def to_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def clean_text(value):
    if isinstance(value, str):
        return " ".join(value.split())
    return value
