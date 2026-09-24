from sqlalchemy.orm import Session

from app.core.time_utils import utc_now
from app.models.notification import Notification, NotificationType


def create(db: Session, notification: Notification) -> Notification:
    db.add(notification)
    db.commit()
    db.refresh(notification)
    return notification


def get_by_id_for_user(db: Session, notification_id: int, user_id: int) -> Notification | None:
    return (
        db.query(Notification)
        .filter(Notification.id == notification_id, Notification.user_id == user_id)
        .first()
    )


def list_paginated(
    db: Session, *, user_id: int, is_read: bool | None, page: int, page_size: int
) -> tuple[list[Notification], int]:
    query = db.query(Notification).filter(Notification.user_id == user_id)
    if is_read is not None:
        query = query.filter(Notification.is_read == is_read)
    total = query.count()
    items = (
        query.order_by(Notification.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return items, total


def count_unread(db: Session, user_id: int) -> int:
    return (
        db.query(Notification)
        .filter(Notification.user_id == user_id, Notification.is_read.is_(False))
        .count()
    )


def has_unread_of_type(db: Session, *, user_id: int, notification_type: NotificationType) -> bool:
    return (
        db.query(Notification)
        .filter(
            Notification.user_id == user_id,
            Notification.type == notification_type,
            Notification.is_read.is_(False),
        )
        .first()
        is not None
    )


def mark_read(db: Session, notification: Notification) -> Notification:
    notification.is_read = True
    notification.read_at = utc_now()
    db.commit()
    db.refresh(notification)
    return notification


def mark_all_read(db: Session, user_id: int) -> int:
    unread = (
        db.query(Notification)
        .filter(Notification.user_id == user_id, Notification.is_read.is_(False))
        .all()
    )
    now = utc_now()
    for notification in unread:
        notification.is_read = True
        notification.read_at = now
    db.commit()
    return len(unread)
