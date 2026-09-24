from fastapi import APIRouter

# Aggregates all versioned (/api/v1/*) routers. Each spec adds its own
# `include_router(...)` call here as it introduces endpoints (auth in
# SPEC 02, master data in SPEC 04, etc.) — kept empty until then.
api_v1_router = APIRouter()
