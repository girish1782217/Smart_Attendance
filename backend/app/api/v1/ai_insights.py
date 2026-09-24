from collections.abc import Callable

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_gemini_generate_fn, require_role
from app.core.database import get_db
from app.core.roles import RoleName
from app.models.user import User
from app.schemas.ai_insight import AIInsightResponse
from app.services import ai_insight_service, scoping

router = APIRouter(prefix="/students", tags=["ai-insights"])


@router.get("/{student_id}/ai-insight", response_model=AIInsightResponse)
def get_ai_insight(
    student_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(RoleName.ADMIN, RoleName.FACULTY, RoleName.STUDENT)),
    generate_fn: Callable[[str], str] = Depends(get_gemini_generate_fn),
) -> AIInsightResponse:
    faculty_scope = scoping.resolve_student_access_scope(db, current_user, student_id)
    insight = ai_insight_service.get_insight(
        db, student_id=student_id, faculty_id_scope=faculty_scope, generate_fn=generate_fn
    )
    return AIInsightResponse(
        student_id=student_id,
        overall=insight["overall"],
        by_subject=insight["by_subject"],
        ai_available=insight["ai_available"],
        insight_text=insight["insight_text"],
        ai_error_code=insight["ai_error_code"],
    )
