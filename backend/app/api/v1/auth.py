from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_bearer_token, get_current_user
from app.core.database import get_db
from app.core.security import decode_access_token
from app.models.user import User
from app.schemas.auth import LoginRequest, TokenResponse
from app.schemas.user import UserResponse
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    user = auth_service.authenticate(db, email=payload.email, password=payload.password)
    token = auth_service.issue_token_for_user(user)
    return TokenResponse(access_token=token)


@router.get("/me", response_model=UserResponse)
def read_current_user(current_user: User = Depends(get_current_user)) -> User:
    return current_user


@router.post("/logout")
def logout(token: str = Depends(get_bearer_token), db: Session = Depends(get_db)) -> dict:
    payload = decode_access_token(token)
    auth_service.logout(db, payload=payload)
    return {"success": True, "message": "Logged out successfully."}
