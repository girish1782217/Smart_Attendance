from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health")
def health_check() -> dict:
    return {"success": True, "status": "ok", "service": "smart-attendance-backend"}
