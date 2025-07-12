# backend/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routers import talks
from core.config import settings

app = FastAPI(
    title=settings.project_name,
    description="API for managing and analyzing Python conference talks",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.backend_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(talks.router, prefix=f"{settings.api_v1_str}/talks", tags=["talks"])


@app.get("/")
async def root():
    return {
        "message": "Python Ireland Talk Database API",
        "version": "2.0.0",
        "database": "PostgreSQL",
        "status": "migrated from Elasticsearch",
    }


@app.get("/health")
async def health():
    """Global health check"""
    return {"status": "healthy", "database": "postgres"}
