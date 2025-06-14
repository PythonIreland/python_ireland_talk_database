# backend/api/routers/talks.py
from fastapi import APIRouter, HTTPException
from models.talk import Talk, TalkSearch
from lib.engine.elasticsearch_client import ElasticsearchClient

router = APIRouter()


@router.get("/")
async def get_talks():
    """Get all talks"""
    return {"talks": [], "message": "Hello from talks API"}


@router.get("/search")
async def search_talks(q: str = None, limit: int = 20):
    """Search talks"""
    return {"query": q, "results": []}


@router.post("/ingest")
async def ingest_data():
    """Ingest data from Sessionize"""
    try:
        from lib.engine.sessionize import Sessionize
        from lib.engine.data_pipeline import DataPipeline

        # Use default events for now
        scraper = Sessionize()
        pipeline = DataPipeline()

        # Get talks from Sessionize
        talks = scraper.get_all_data()

        # Process and store in Elasticsearch
        pipeline.ingest_talks(talks)

        return {
            "message": "Data ingestion completed successfully",
            "talks_processed": len(talks),
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {str(e)}")


@router.get("/health")
async def health_check():
    """Check if Elasticsearch is available"""
    try:
        es_client = ElasticsearchClient()
        # Simple health check
        return {"status": "healthy", "elasticsearch": "connected"}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}
