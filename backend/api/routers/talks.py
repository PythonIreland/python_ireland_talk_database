# backend/api/routers/talks.py
from fastapi import APIRouter, HTTPException, Query
from models.talk import TalkSearch, TalkType
from lib.engine.elasticsearch_client import ElasticsearchClient
from typing import List, Optional

router = APIRouter()


@router.get("/")
async def get_talks(
    talk_types: Optional[List[TalkType]] = Query(None), limit: int = 20, offset: int = 0
):
    """Get talks with optional type filtering"""
    es_client = ElasticsearchClient()

    query = {"query": {"match_all": {}}, "size": limit, "from": offset}

    if talk_types:
        query["query"] = {"terms": {"talk_type": [t.value for t in talk_types]}}

    try:
        results = es_client.search_talks(query)
        return {"talks": results, "total": len(results)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search")
async def search_talks(
    q: Optional[str] = None,
    talk_types: Optional[List[TalkType]] = Query(None),
    tags: Optional[str] = None,
    limit: int = 20,
):
    """Search talks with filters"""
    es_client = ElasticsearchClient()

    # Build query
    query = {"query": {"bool": {"must": []}}, "size": limit}

    if q:
        query["query"]["bool"]["must"].append(
            {
                "multi_match": {
                    "query": q,
                    "fields": ["title^2", "description", "speaker_names"],
                }
            }
        )

    if talk_types:
        query["query"]["bool"]["must"].append(
            {"terms": {"talk_type": [t.value for t in talk_types]}}
        )

    if tags:
        tag_list = tags.split(",")
        query["query"]["bool"]["must"].append({"terms": {"auto_tags": tag_list}})

    if not query["query"]["bool"]["must"]:
        query = {"query": {"match_all": {}}, "size": limit}

    try:
        results = es_client.search_talks(query)
        return {"talks": results, "total": len(results)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ingest")
async def ingest_all_data():
    """Ingest data from all sources"""
    try:
        from lib.engine.data_pipeline import DataPipeline

        pipeline = DataPipeline()
        results = pipeline.ingest_all_data()

        return {
            "message": "Data ingestion completed successfully",
            "results": results,
            "total_processed": sum(results.values()),
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {str(e)}")


# backend/api/routers/talks.py - add this endpoint
@router.get("/health")
async def health_check():
    """Check if Elasticsearch is available"""
    try:
        es_client = ElasticsearchClient()
        if es_client.is_healthy():
            talk_count = es_client.get_talk_count()
            return {
                "status": "healthy",
                "elasticsearch": "connected",
                "talk_count": talk_count,
            }
        else:
            return {
                "status": "unhealthy",
                "elasticsearch": "disconnected",
                "talk_count": 0,
            }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Health check failed: {str(e)}")


@router.get("/types")
async def get_talk_types():
    """Get available talk types"""
    return {"types": [t.value for t in TalkType]}
