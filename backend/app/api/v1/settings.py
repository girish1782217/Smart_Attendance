from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_role
from app.core.database import get_db
from app.core.roles import RoleName
from app.schemas.settings import LowAttendanceThresholdResponse, LowAttendanceThresholdUpdateRequest
from app.services import settings_service

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("/low-attendance-threshold", response_model=LowAttendanceThresholdResponse)
def get_low_attendance_threshold(
    db: Session = Depends(get_db), _current_user=Depends(get_current_user)
) -> LowAttendanceThresholdResponse:
    return LowAttendanceThresholdResponse(threshold=settings_service.get_low_attendance_threshold(db))


@router.put("/low-attendance-threshold", response_model=LowAttendanceThresholdResponse)
def set_low_attendance_threshold(
    payload: LowAttendanceThresholdUpdateRequest,
    db: Session = Depends(get_db),
    _current_user=Depends(require_role(RoleName.ADMIN)),
) -> LowAttendanceThresholdResponse:
    threshold = settings_service.set_low_attendance_threshold(db, payload.threshold)
    return LowAttendanceThresholdResponse(threshold=threshold)
