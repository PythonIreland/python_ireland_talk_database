# backend/api/routers/talks.py
from fastapi import APIRouter, HTTPException, Query, Depends
from backend.domain.models import (
    TalkSearch,
    TalkType,
    CreateTaxonomyRequest,
    UpdateTaxonomyRequest,
    CreateTaxonomyValueRequest,
    UpdateTaxonomyValueRequest,
    AddTagsRequest,
    ReplaceTalkTagsRequest,
)
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


# Enhanced taxonomy CRUD endpoints
@router.post("/taxonomies")
async def create_taxonomy(
    taxonomy_data: CreateTaxonomyRequest,
    talk_service: TalkService = Depends(get_talk_service),
):
    """Create a new taxonomy"""
    try:
        taxonomy_id = talk_service.create_taxonomy(
            name=taxonomy_data.name,
            description=taxonomy_data.description,
            created_by=taxonomy_data.created_by,
        )
        return {"id": taxonomy_id, "message": "Taxonomy created successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/taxonomies/{taxonomy_id}")
async def update_taxonomy(
    taxonomy_id: int,
    taxonomy_data: UpdateTaxonomyRequest,
    talk_service: TalkService = Depends(get_talk_service),
):
    """Update existing taxonomy"""
    try:
        success = talk_service.update_taxonomy(
            taxonomy_id=taxonomy_id,
            name=taxonomy_data.name,
            description=taxonomy_data.description,
        )
        if not success:
            raise HTTPException(status_code=404, detail="Taxonomy not found")
        return {"message": "Taxonomy updated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/taxonomies/{taxonomy_id}")
async def delete_taxonomy(
    taxonomy_id: int, talk_service: TalkService = Depends(get_talk_service)
):
    """Delete taxonomy (cascade to values)"""
    try:
        success = talk_service.delete_taxonomy(taxonomy_id)
        if not success:
            raise HTTPException(status_code=404, detail="Taxonomy not found")
        return {"message": "Taxonomy deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/taxonomies/{taxonomy_id}/values")
async def create_taxonomy_value(
    taxonomy_id: int,
    value_data: CreateTaxonomyValueRequest,
    talk_service: TalkService = Depends(get_talk_service),
):
    """Add value to taxonomy"""
    try:
        value_id = talk_service.create_taxonomy_value(
            taxonomy_id=taxonomy_id,
            value=value_data.value,
            description=value_data.description,
            color=value_data.color,
        )
        return {"id": value_id, "message": "Taxonomy value created successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/taxonomy-values/{value_id}")
async def update_taxonomy_value(
    value_id: int,
    value_data: UpdateTaxonomyValueRequest,
    talk_service: TalkService = Depends(get_talk_service),
):
    """Update taxonomy value"""
    try:
        success = talk_service.update_taxonomy_value(
            value_id=value_id,
            value=value_data.value,
            description=value_data.description,
            color=value_data.color,
        )
        if not success:
            raise HTTPException(status_code=404, detail="Taxonomy value not found")
        return {"message": "Taxonomy value updated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/taxonomy-values/{value_id}")
async def delete_taxonomy_value(
    value_id: int, talk_service: TalkService = Depends(get_talk_service)
):
    """Delete taxonomy value"""
    try:
        success = talk_service.delete_taxonomy_value(value_id)
        if not success:
            raise HTTPException(status_code=404, detail="Taxonomy value not found")
        return {"message": "Taxonomy value deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Enhanced talk tagging endpoints
@router.get("/talks/{talk_id}/tags")
async def get_talk_tags(
    talk_id: str, talk_service: TalkService = Depends(get_talk_service)
):
    """Get all tags for a talk (grouped by taxonomy)"""
    try:
        tags = talk_service.get_talk_tags_grouped(talk_id)
        if not tags:
            raise HTTPException(status_code=404, detail="Talk not found")
        return tags
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/talks/{talk_id}/tags")
async def replace_talk_tags(
    talk_id: str,
    tag_data: ReplaceTalkTagsRequest,
    talk_service: TalkService = Depends(get_talk_service),
):
    """Replace all manual tags for a talk"""
    try:
        success = talk_service.replace_talk_tags(talk_id, tag_data.taxonomy_value_ids)
        if not success:
            raise HTTPException(status_code=404, detail="Talk not found")
        return {"message": "Tags replaced successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/talks/{talk_id}/tags/add")
async def add_tags_to_talk(
    talk_id: str,
    tag_data: AddTagsRequest,
    talk_service: TalkService = Depends(get_talk_service),
):
    """Add specific tags to a talk"""
    try:
        success = talk_service.add_tags_to_talk(talk_id, tag_data.taxonomy_value_ids)
        if not success:
            raise HTTPException(status_code=404, detail="Talk not found")
        return {"message": "Tags added successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/talks/{talk_id}/tags/{value_id}")
async def remove_tag_from_talk(
    talk_id: str, value_id: int, talk_service: TalkService = Depends(get_talk_service)
):
    """Remove specific tag from talk"""
    try:
        success = talk_service.remove_tag_from_talk(talk_id, value_id)
        if not success:
            raise HTTPException(status_code=404, detail="Talk or tag not found")
        return {"message": "Tag removed successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Individual talk routes (put at end to avoid conflicts with specific routes)
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
