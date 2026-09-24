from fastapi import APIRouter

from app.api.v1.auth import router as auth_router
from app.api.v1.master_data import master_data_router
from app.api.v1.students import router as students_router
from app.api.v1.users import router as users_router

# Aggregates all versioned (/api/v1/*) routers. Each spec adds its own
# `include_router(...)` call here as it introduces endpoints.
api_v1_router = APIRouter()
api_v1_router.include_router(auth_router)
api_v1_router.include_router(users_router)
api_v1_router.include_router(master_data_router)
api_v1_router.include_router(students_router)
