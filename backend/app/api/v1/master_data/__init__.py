from fastapi import APIRouter

from app.api.v1.master_data.academic_class import router as classes_router
from app.api.v1.master_data.academic_year import router as academic_years_router
from app.api.v1.master_data.department import router as departments_router
from app.api.v1.master_data.program import router as programs_router
from app.api.v1.master_data.section import router as sections_router
from app.api.v1.master_data.semester import router as semesters_router
from app.api.v1.master_data.subject import router as subjects_router

master_data_router = APIRouter()
master_data_router.include_router(departments_router)
master_data_router.include_router(programs_router)
master_data_router.include_router(academic_years_router)
master_data_router.include_router(semesters_router)
master_data_router.include_router(classes_router)
master_data_router.include_router(sections_router)
master_data_router.include_router(subjects_router)
