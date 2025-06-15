# backend/run.py - fix the uvicorn.run call
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routers import talks

app = FastAPI(title="Python Ireland Talk Database API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(talks.router, prefix="/api/v1/talks", tags=["talks"])

if __name__ == "__main__":
    import uvicorn

    # Use import string instead of app object for reload to work
    uvicorn.run("run:app", host="0.0.0.0", port=8000, reload=True)
