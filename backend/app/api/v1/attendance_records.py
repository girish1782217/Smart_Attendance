from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import require_role
from app.core.database import get_db
from app.core.roles import RoleName
from app.models.user import User
from app.schemas.correction import CorrectionCreateRequest, CorrectionResponse
from app.services import correction_service

router = APIRouter(prefix="/attendance-records", tags=["attendance-records"])


@router.post("/{attendance_record_id}/corrections", response_model=CorrectionResponse, status_code=201)
def request_correction(
    attendance_record_id: int,
    payload: CorrectionCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(RoleName.ADMIN, RoleName.FACULTY, RoleName.STUDENT)),
) -> CorrectionResponse:
    correction = correction_service.request_correction(
        db,
        attendance_record_id=attendance_record_id,
        requested_status=payload.requested_status,
        reason=payload.reason,
        current_user=current_user,
    )
    return CorrectionResponse.from_model(correction)
