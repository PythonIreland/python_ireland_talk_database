# backend/api/routers/talks.py
from fastapi import APIRouter, HTTPException, Query, Depends
from backend.domain.models import TalkSearch, TalkType
from backend.services.talk_service import TalkService
from typing import List, Optional

router = APIRouter()


# Dependency to get TalkService
def get_talk_service() -> TalkService:
    return TalkService()


@router.get("/")
async def get_talks(
    talk_types: Optional[List[TalkType]] = Query(None),
    limit: int = 20,
    offset: int = 0,
    talk_service: TalkService = Depends(get_talk_service),
):
    """Get talks with optional type filtering"""
    try:
        talks, total = talk_service.search_talks(
            talk_types=talk_types, limit=limit, offset=offset
        )
        return {"talks": talks, "total": total}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search")
async def search_talks(
    q: Optional[str] = None,
    talk_types: Optional[List[TalkType]] = Query(None),
    tags: Optional[str] = None,
    events: Optional[str] = None,
    cities: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
    talk_service: TalkService = Depends(get_talk_service),
):
    """Search talks with filters"""
    try:
        # Parse comma-separated values
        tag_list = tags.split(",") if tags else None
        event_list = events.split(",") if events else None
        city_list = cities.split(",") if cities else None

        talks, total = talk_service.search_talks(
            query=q,
            talk_types=talk_types,
            tags=tag_list,
            events=event_list,
            cities=city_list,
            limit=limit,
            offset=offset,
        )
        return {"talks": talks, "total": total}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{talk_id}")
async def get_talk(talk_id: str, talk_service: TalkService = Depends(get_talk_service)):
    """Get a single talk by ID"""
    try:
        talk = talk_service.get_talk(talk_id)
        if not talk:
            raise HTTPException(status_code=404, detail="Talk not found")
        return talk
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ingest")
async def ingest_all_data(talk_service: TalkService = Depends(get_talk_service)):
    """Ingest data from all sources"""
    try:
        from lib.engine.data_pipeline import DataPipeline

        # Initialize database if needed
        talk_service.init_database()

        # Initialize default taxonomies
        talk_service.initialize_default_taxonomies()

        pipeline = DataPipeline(talk_service=talk_service)
        results = pipeline.ingest_all_data()

        return {
            "message": "Data ingestion completed successfully",
            "results": results,
            "total_processed": sum(results.values()),
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {str(e)}")


@router.get("/health")
async def health_check(talk_service: TalkService = Depends(get_talk_service)):
    """Check if database is available"""
    try:
        if talk_service.is_healthy():
            talk_count = talk_service.get_talk_count()
            return {
                "status": "healthy",
                "database": "connected",
                "talk_count": talk_count,
            }
        else:
            return {
                "status": "unhealthy",
                "database": "disconnected",
                "talk_count": 0,
            }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Health check failed: {str(e)}")


@router.get("/types")
async def get_talk_types():
    """Get available talk types"""
    return {"types": [t.value for t in TalkType]}


@router.get("/events")
async def get_events(talk_service: TalkService = Depends(get_talk_service)):
    """Get all event names"""
    try:
        events = talk_service.get_events()
        return {"events": events}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tags")
async def get_tags(talk_service: TalkService = Depends(get_talk_service)):
    """Get all auto tags with counts"""
    try:
        tags = talk_service.get_tags()
        return {"tags": tags}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Taxonomy management endpoints


@router.get("/taxonomies")
async def get_taxonomies(talk_service: TalkService = Depends(get_talk_service)):
    """Get all taxonomies"""
    try:
        taxonomies = talk_service.get_taxonomies()
        return {"taxonomies": taxonomies}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{talk_id}/tags")
async def update_talk_tags(
    talk_id: str,
    taxonomy_value_ids: List[int],
    talk_service: TalkService = Depends(get_talk_service),
):
    """Update manual tags for a talk"""
    try:
        success = talk_service.update_talk_tags(talk_id, taxonomy_value_ids)
        if not success:
            raise HTTPException(status_code=404, detail="Talk not found")
        return {"message": "Tags updated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
