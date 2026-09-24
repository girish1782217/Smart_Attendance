from sqlalchemy.orm import Session

from app.models.system_setting import SystemSetting


def get(db: Session, key: str) -> SystemSetting | None:
    return db.get(SystemSetting, key)


def set_value(db: Session, key: str, value: str) -> SystemSetting:
    setting = db.get(SystemSetting, key)
    if setting is None:
        setting = SystemSetting(key=key, value=value)
        db.add(setting)
    else:
        setting.value = value
    db.commit()
    db.refresh(setting)
    return setting
