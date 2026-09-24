from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.exceptions import ValidationAppError
from app.repositories import system_setting_repository

LOW_ATTENDANCE_THRESHOLD_KEY = "LOW_ATTENDANCE_THRESHOLD"


def get_low_attendance_threshold(db: Session) -> float:
    setting = system_setting_repository.get(db, LOW_ATTENDANCE_THRESHOLD_KEY)
    if setting is None:
        # Falls back to the .env-configured default (never hardcoded here)
        # until an admin explicitly sets one via PUT.
        return get_settings().low_attendance_default_threshold
    return float(setting.value)


def set_low_attendance_threshold(db: Session, threshold: float) -> float:
    if not (0 < threshold <= 100):
        raise ValidationAppError(
            "Threshold must be greater than 0 and at most 100.", code="INVALID_THRESHOLD"
        )
    setting = system_setting_repository.set_value(db, LOW_ATTENDANCE_THRESHOLD_KEY, str(threshold))
    return float(setting.value)
