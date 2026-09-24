from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.models.attendance_session import AttendanceSession
from app.models.correction_request import CorrectionRequest
from app.models.notification import Notification, NotificationType
from app.repositories import faculty_repository, notification_repository, student_repository
from app.services import attendance_history_service, settings_service


def notify(
    db: Session,
    *,
    user_id: int,
    notification_type: NotificationType,
    title: str,
    message: str,
    related_entity_type: str | None = None,
    related_entity_id: int | None = None,
) -> Notification:
    notification = Notification(
        user_id=user_id,
        type=notification_type,
        title=title,
        message=message,
        related_entity_type=related_entity_type,
        related_entity_id=related_entity_id,
    )
    return notification_repository.create(db, notification)


def notify_correction_requested(
    db: Session, *, correction: CorrectionRequest, session: AttendanceSession, requester_user_id: int
) -> None:
    faculty = faculty_repository.get_by_id(db, session.faculty_id)
    if faculty is None or faculty.user_id == requester_user_id:
        return  # self-requested by the owning faculty -- nothing to notify via this channel
    notify(
        db,
        user_id=faculty.user_id,
        notification_type=NotificationType.CORRECTION_REQUESTED,
        title="New attendance correction request",
        message=f"A correction request was submitted for attendance record #{correction.attendance_record_id}.",
        related_entity_type="correction_request",
        related_entity_id=correction.id,
    )


def notify_correction_decided(db: Session, *, correction: CorrectionRequest, approved: bool) -> None:
    notify(
        db,
        user_id=correction.requested_by_user_id,
        notification_type=(
            NotificationType.CORRECTION_APPROVED if approved else NotificationType.CORRECTION_REJECTED
        ),
        title=f"Your attendance correction request was {'approved' if approved else 'rejected'}",
        message=correction.decision_reason or "No decision reason was provided.",
        related_entity_type="correction_request",
        related_entity_id=correction.id,
    )


def check_and_notify_low_attendance(db: Session, student_ids: list[int]) -> None:
    threshold = settings_service.get_low_attendance_threshold(db)
    for student_id in student_ids:
        summary = attendance_history_service.get_summary(db, student_id=student_id, faculty_id=None)
        percentage = summary["overall"]["percentage"]
        if percentage is None or percentage >= threshold:
            continue

        student = student_repository.get_by_id(db, student_id)
        if notification_repository.has_unread_of_type(
            db, user_id=student.user_id, notification_type=NotificationType.LOW_ATTENDANCE_WARNING
        ):
            continue  # duplicate prevention: don't pile up repeat unread alerts

        notify(
            db,
            user_id=student.user_id,
            notification_type=NotificationType.LOW_ATTENDANCE_WARNING,
            title="Low attendance warning",
            message=f"Your overall attendance is {percentage}%, below the {threshold}% threshold.",
            related_entity_type="student",
            related_entity_id=student_id,
        )


def list_for_user(
    db: Session, *, user_id: int, is_read: bool | None, page: int, page_size: int
) -> tuple[list[Notification], int]:
    return notification_repository.list_paginated(
        db, user_id=user_id, is_read=is_read, page=page, page_size=page_size
    )


def count_unread(db: Session, user_id: int) -> int:
    return notification_repository.count_unread(db, user_id)


def mark_read(db: Session, *, notification_id: int, user_id: int) -> Notification:
    notification = notification_repository.get_by_id_for_user(db, notification_id, user_id)
    if notification is None:
        raise NotFoundError("Notification not found.", code="NOTIFICATION_NOT_FOUND")
    return notification_repository.mark_read(db, notification)


def mark_all_read(db: Session, user_id: int) -> int:
    return notification_repository.mark_all_read(db, user_id)
