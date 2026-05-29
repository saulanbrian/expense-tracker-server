from fastapi import APIRouter
from ..features.ingestion.router import router as ingestion_router

api_router = APIRouter()

api_router.include_router(ingestion_router)
