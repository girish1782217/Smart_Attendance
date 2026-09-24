from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_bearer_token, get_current_user
from app.core.database import get_db
from app.core.security import decode_access_token
from app.models.user import User
from app.repositories import faculty_repository, student_repository
from app.schemas.auth import LoginRequest, TokenResponse
from app.schemas.user import UserWithRolesResponse
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    user = auth_service.authenticate(db, email=payload.email, password=payload.password)
    token = auth_service.issue_token_for_user(user)
    return TokenResponse(access_token=token)


@router.get("/me", response_model=UserWithRolesResponse)
def read_current_user(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UserWithRolesResponse:
    # Roles are included (unlike the plain UserResponse SPEC 02 originally
    # shipped) so the frontend can route/render by role without a separate
    # call — see docs/sdd/00-product-spec.md's frontend architecture note.
    # student_id/faculty_id are resolved the same way for the same reason:
    # a STUDENT has no other endpoint that reveals their own Student.id,
    # which every /students/{id}/... route requires as a path param.
    student = student_repository.get_by_user_id(db, current_user.id)
    faculty = faculty_repository.get_by_user_id(db, current_user.id)
    return UserWithRolesResponse.from_model(
        current_user,
        student_id=student.id if student else None,
        faculty_id=faculty.id if faculty else None,
    )


@router.post("/logout")
def logout(token: str = Depends(get_bearer_token), db: Session = Depends(get_db)) -> dict:
    payload = decode_access_token(token)
    auth_service.logout(db, payload=payload)
    return {"success": True, "message": "Logged out successfully."}
