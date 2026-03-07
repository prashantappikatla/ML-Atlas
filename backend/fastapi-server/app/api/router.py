from fastapi import APIRouter
from .v1 import algorithms, categories, labs, notes, search, status

api_router = APIRouter()

api_router.include_router(algorithms.router, prefix="/algorithms", tags=["algorithms"])
api_router.include_router(categories.router, prefix="/categories", tags=["categories"])
api_router.include_router(labs.router, prefix="/labs", tags=["labs"])
api_router.include_router(notes.router, prefix="/notes", tags=["notes"])
api_router.include_router(search.router, prefix="/search", tags=["search"])
api_router.include_router(status.router, prefix="/status", tags=["status"])
