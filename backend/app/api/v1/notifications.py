from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.notification import NotificationResponse
from app.schemas.pagination import Page, PaginationParams
from app.services import notification_service

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("", response_model=Page[NotificationResponse])
def list_notifications(
    pagination: PaginationParams = Depends(),
    is_read: bool | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Page[NotificationResponse]:
    items, total = notification_service.list_for_user(
        db, user_id=current_user.id, is_read=is_read, page=pagination.page, page_size=pagination.page_size
    )
    return Page(
        items=[NotificationResponse.model_validate(item) for item in items],
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
    )


@router.get("/unread-count")
def get_unread_count(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
) -> dict:
    return {"count": notification_service.count_unread(db, current_user.id)}


@router.post("/{notification_id}/read", response_model=NotificationResponse)
def mark_notification_read(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> NotificationResponse:
    notification = notification_service.mark_read(
        db, notification_id=notification_id, user_id=current_user.id
    )
    return NotificationResponse.model_validate(notification)


@router.post("/mark-all-read")
def mark_all_notifications_read(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
) -> dict:
    marked_count = notification_service.mark_all_read(db, current_user.id)
    return {"marked_count": marked_count}
