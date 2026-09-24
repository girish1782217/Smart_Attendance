from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, ForbiddenError, NotFoundError, ValidationAppError
from app.core.roles import RoleName
from app.core.time_utils import utc_now
from app.models.attendance_record import AttendanceRecord, AttendanceStatus
from app.models.attendance_session import AttendanceSession, AttendanceSessionStatus
from app.models.audit_log import AuditAction
from app.models.correction_request import CorrectionRequest, CorrectionRequestStatus
from app.models.user import User
from app.repositories import attendance_record_repository, correction_repository
from app.services import audit_service, scoping


def _role_names(user: User) -> set[str]:
    return {role.name for role in user.roles}


def _ensure_can_request(
    db: Session, current_user: User, record: AttendanceRecord, session: AttendanceSession
) -> None:
    roles = _role_names(current_user)
    if RoleName.ADMIN.value in roles:
        return
    if RoleName.FACULTY.value in roles:
        faculty_id = scoping.resolve_faculty_filter(db, current_user, None)
        if session.faculty_id != faculty_id:
            raise ForbiddenError("You do not own this attendance session.", code="FORBIDDEN")
        return
    if RoleName.STUDENT.value in roles:
        student_id = scoping.resolve_own_student_id(db, current_user)
        if record.student_id != student_id:
            raise ForbiddenError(
                "You can only request corrections for your own attendance record.", code="FORBIDDEN"
            )
        return
    raise ForbiddenError("You do not have permission to perform this action.", code="FORBIDDEN")


def _ensure_can_review(
    db: Session, current_user: User, correction: CorrectionRequest, session: AttendanceSession
) -> None:
    roles = _role_names(current_user)
    if RoleName.ADMIN.value in roles:
        return
    if RoleName.FACULTY.value not in roles:
        raise ForbiddenError("You do not have permission to perform this action.", code="FORBIDDEN")

    faculty_id = scoping.resolve_faculty_filter(db, current_user, None)
    if session.faculty_id != faculty_id:
        raise ForbiddenError("You do not own this attendance session.", code="FORBIDDEN")
    if correction.requested_by_user_id == current_user.id:
        raise ForbiddenError(
            "You cannot review a correction you requested yourself; escalate to an admin.",
            code="SELF_REVIEW_NOT_ALLOWED",
        )


def request_correction(
    db: Session,
    *,
    attendance_record_id: int,
    requested_status: AttendanceStatus,
    reason: str,
    current_user: User,
) -> CorrectionRequest:
    record = attendance_record_repository.get_by_id(db, attendance_record_id)
    if record is None:
        raise NotFoundError("Attendance record not found.", code="ATTENDANCE_RECORD_NOT_FOUND")

    session = record.session
    if session.status != AttendanceSessionStatus.SUBMITTED:
        raise ConflictError(
            "Corrections can only be requested for finalized (submitted) sessions.",
            code="SESSION_NOT_SUBMITTED",
        )

    _ensure_can_request(db, current_user, record, session)

    if requested_status == record.status:
        raise ValidationAppError(
            "Requested status must differ from the record's current status.", code="NO_CHANGE_REQUESTED"
        )

    if correction_repository.get_pending_for_record(db, attendance_record_id) is not None:
        raise ConflictError(
            "A correction request is already pending for this record.", code="CORRECTION_ALREADY_PENDING"
        )

    correction = CorrectionRequest(
        attendance_record_id=attendance_record_id,
        original_status=record.status,
        requested_status=requested_status,
        reason=reason,
        requested_by_user_id=current_user.id,
        status=CorrectionRequestStatus.PENDING,
    )
    correction = correction_repository.create(db, correction)

    audit_service.log(
        db,
        actor_user_id=current_user.id,
        action=AuditAction.CORRECTION_REQUESTED,
        entity_type="attendance_record",
        entity_id=attendance_record_id,
        before_value=record.status.value,
        after_value=requested_status.value,
        reason=reason,
    )
    return correction_repository.get_by_id(db, correction.id)


def get_correction(db: Session, correction_id: int) -> CorrectionRequest:
    correction = correction_repository.get_by_id(db, correction_id)
    if correction is None:
        raise NotFoundError("Correction request not found.", code="CORRECTION_NOT_FOUND")
    return correction


def ensure_can_view(db: Session, current_user: User, correction: CorrectionRequest) -> None:
    roles = _role_names(current_user)
    if RoleName.ADMIN.value in roles:
        return
    session = correction.attendance_record.session
    if RoleName.FACULTY.value in roles:
        faculty_id = scoping.resolve_faculty_filter(db, current_user, None)
        if session.faculty_id == faculty_id:
            return
    if RoleName.STUDENT.value in roles:
        student_id = scoping.resolve_own_student_id(db, current_user)
        if correction.attendance_record.student_id == student_id:
            return
    raise ForbiddenError("You do not have access to this correction request.", code="FORBIDDEN")


def list_corrections(
    db: Session,
    *,
    page: int,
    page_size: int,
    status: CorrectionRequestStatus | None,
    attendance_record_id: int | None,
    faculty_id: int | None,
    student_id: int | None,
) -> tuple[list[CorrectionRequest], int]:
    return correction_repository.list_paginated(
        db,
        page=page,
        page_size=page_size,
        status=status,
        attendance_record_id=attendance_record_id,
        faculty_id=faculty_id,
        student_id=student_id,
    )


def approve_correction(
    db: Session, *, correction_id: int, current_user: User, decision_reason: str | None
) -> CorrectionRequest:
    correction = get_correction(db, correction_id)
    if correction.status != CorrectionRequestStatus.PENDING:
        raise ConflictError(
            "This correction request has already been decided.", code="CORRECTION_ALREADY_DECIDED"
        )

    record = correction.attendance_record
    session = record.session
    _ensure_can_review(db, current_user, correction, session)

    original_value = record.status.value
    record.status = correction.requested_status
    record.recorded_by_user_id = current_user.id

    correction.status = CorrectionRequestStatus.APPROVED
    correction.reviewed_by_user_id = current_user.id
    correction.reviewed_at = utc_now()
    correction.decision_reason = decision_reason

    db.commit()

    audit_service.log(
        db,
        actor_user_id=current_user.id,
        action=AuditAction.CORRECTION_APPROVED,
        entity_type="attendance_record",
        entity_id=record.id,
        before_value=original_value,
        after_value=correction.requested_status.value,
        reason=decision_reason,
    )
    return get_correction(db, correction_id)


def reject_correction(
    db: Session, *, correction_id: int, current_user: User, decision_reason: str | None
) -> CorrectionRequest:
    correction = get_correction(db, correction_id)
    if correction.status != CorrectionRequestStatus.PENDING:
        raise ConflictError(
            "This correction request has already been decided.", code="CORRECTION_ALREADY_DECIDED"
        )

    session = correction.attendance_record.session
    _ensure_can_review(db, current_user, correction, session)

    correction.status = CorrectionRequestStatus.REJECTED
    correction.reviewed_by_user_id = current_user.id
    correction.reviewed_at = utc_now()
    correction.decision_reason = decision_reason
    db.commit()

    audit_service.log(
        db,
        actor_user_id=current_user.id,
        action=AuditAction.CORRECTION_REJECTED,
        entity_type="attendance_record",
        entity_id=correction.attendance_record_id,
        before_value=correction.original_status.value,
        after_value=correction.original_status.value,
        reason=decision_reason,
    )
    return get_correction(db, correction_id)
