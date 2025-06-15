# backend/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routers import talks
from core.config import settings

app = FastAPI(
    title="Python Ireland Talk Database",
    description="API for managing and analyzing Python conference talks",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(talks.router, prefix="/api/v1/talks", tags=["talks"])


@app.get("/")
async def root():
    return {"message": "Python Ireland Talk Database API"}
