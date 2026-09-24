from fastapi import APIRouter

from app.api.v1.attendance_records import router as attendance_records_router
from app.api.v1.attendance_sessions import router as attendance_sessions_router
from app.api.v1.auth import router as auth_router
from app.api.v1.corrections import router as corrections_router
from app.api.v1.faculty import router as faculty_router
from app.api.v1.faculty_assignments import router as faculty_assignments_router
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
api_v1_router.include_router(faculty_router)
api_v1_router.include_router(faculty_assignments_router)
api_v1_router.include_router(attendance_sessions_router)
api_v1_router.include_router(attendance_records_router)
api_v1_router.include_router(corrections_router)
