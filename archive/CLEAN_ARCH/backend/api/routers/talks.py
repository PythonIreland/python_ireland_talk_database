# backend/api/routers/talks.py
from fastapi import APIRouter, HTTPException, Query, Depends
from backend.contracts.dtos import (
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
from typing import List, Optional, Dict

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
    """Ingest data from all sources (full reload)"""
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


@router.post("/sync")
async def sync_incremental_data(talk_service: TalkService = Depends(get_talk_service)):
    """Sync only new and updated talks from all sources"""
    try:
        from lib.engine.data_pipeline import DataPipeline

        # Initialize database if needed
        talk_service.init_database()

        # Initialize default taxonomies if needed
        talk_service.initialize_default_taxonomies()

        pipeline = DataPipeline(talk_service=talk_service)
        results = pipeline.sync_incremental_data()

        # Ensure all values are integers, not None
        safe_results = {
            "new_meetup": results.get("new_meetup", 0) or 0,
            "updated_meetup": results.get("updated_meetup", 0) or 0,
            "new_sessionize": results.get("new_sessionize", 0) or 0,
            "updated_sessionize": results.get("updated_sessionize", 0) or 0,
            "errors": results.get("errors", 0) or 0,
        }

        total_processed = (
            safe_results["new_meetup"]
            + safe_results["updated_meetup"]
            + safe_results["new_sessionize"]
            + safe_results["updated_sessionize"]
        )

        return {
            "message": "Incremental sync completed successfully",
            "results": safe_results,
            "total_processed": total_processed,
            "errors": safe_results["errors"],
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Sync failed: {str(e)}")


@router.get("/sync/status")
async def get_sync_status(talk_service: TalkService = Depends(get_talk_service)):
    """Get synchronization status for all data sources"""
    try:
        sync_statuses = talk_service.get_all_sync_statuses()

        # Add some summary statistics
        total_talks = talk_service.get_talk_count()

        return {
            "sync_statuses": sync_statuses,
            "summary": {
                "total_talks": total_talks,
                "total_sources": len(sync_statuses),
                "last_activity": max(
                    [
                        s.get("last_sync_time")
                        for s in sync_statuses
                        if s.get("last_sync_time")
                    ]
                    + [""]
                ),
            },
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get sync status: {str(e)}"
        )


@router.get("/sync/status/{source_type}")
async def get_source_sync_status(
    source_type: str, talk_service: TalkService = Depends(get_talk_service)
):
    """Get synchronization status for a specific data source"""
    try:
        sync_status = talk_service.get_sync_status(source_type)

        if not sync_status:
            return {
                "source_type": source_type,
                "message": "No sync history found for this source",
                "sync_status": None,
            }

        return {"source_type": source_type, "sync_status": sync_status}

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get sync status: {str(e)}"
        )


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


# ===== PHASE 2: ENHANCED SERVICE LAYER FEATURES =====


# Analytics endpoints
@router.get("/analytics/taxonomy-usage")
async def get_taxonomy_usage_analytics(
    talk_service: TalkService = Depends(get_talk_service),
):
    """Get usage statistics for all taxonomies"""
    try:
        stats = talk_service.get_taxonomy_usage_stats()
        return {"analytics": stats}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analytics/popular-tags")
async def get_popular_tags(
    limit: int = Query(20, description="Number of tags to return"),
    talk_service: TalkService = Depends(get_talk_service),
):
    """Get most popular tags across all taxonomies"""
    try:
        tags = talk_service.get_most_popular_tags(limit=limit)
        return {"popular_tags": tags}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analytics/taxonomy/{taxonomy_id}/usage")
async def get_taxonomy_value_usage(
    taxonomy_id: int, talk_service: TalkService = Depends(get_talk_service)
):
    """Get usage statistics for values in a specific taxonomy"""
    try:
        stats = talk_service.get_taxonomy_value_counts(taxonomy_id)
        return {"taxonomy_id": taxonomy_id, "value_usage": stats}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Bulk operations endpoints
@router.post("/bulk/tag-operations")
async def bulk_tag_operations(
    operations: List[Dict], talk_service: TalkService = Depends(get_talk_service)
):
    """Perform bulk tag operations for efficiency

    Example operations:
    [
        {"action": "add", "talk_id": "talk1", "taxonomy_value_ids": [1, 2]},
        {"action": "remove", "talk_id": "talk2", "taxonomy_value_id": 3},
        {"action": "replace", "talk_id": "talk3", "taxonomy_value_ids": [4, 5]}
    ]
    """
    try:
        success = talk_service.bulk_update_talk_tags(operations)
        if not success:
            raise HTTPException(status_code=400, detail="Some operations failed")
        return {"message": f"Successfully processed {len(operations)} operations"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Enhanced search with taxonomy filtering
@router.get("/search/advanced")
async def advanced_search_talks(
    q: Optional[str] = Query(None, description="Text search query"),
    talk_types: Optional[List[TalkType]] = Query(
        None, description="Filter by talk types"
    ),
    taxonomy_filters: Optional[str] = Query(
        None, description="JSON string of taxonomy filters"
    ),
    difficulty: Optional[List[str]] = Query(
        None, description="Filter by difficulty levels"
    ),
    topics: Optional[List[str]] = Query(None, description="Filter by topic areas"),
    conferences: Optional[List[str]] = Query(None, description="Filter by conferences"),
    limit: int = Query(20, description="Number of results to return"),
    offset: int = Query(0, description="Offset for pagination"),
    talk_service: TalkService = Depends(get_talk_service),
):
    """Advanced search with taxonomy-based filtering"""
    try:
        import json

        # Parse taxonomy filters if provided
        parsed_filters = {}
        if taxonomy_filters:
            try:
                parsed_filters = json.loads(taxonomy_filters)
            except json.JSONDecodeError:
                raise HTTPException(
                    status_code=400, detail="Invalid taxonomy_filters JSON"
                )

        # Build taxonomy filters from individual parameters
        if difficulty:
            parsed_filters["difficulty"] = difficulty
        if topics:
            parsed_filters["topic"] = topics
        if conferences:
            parsed_filters["conference"] = conferences

        talks, total = talk_service.advanced_search_talks(
            query=q,
            talk_types=talk_types,
            taxonomy_filters=parsed_filters,
            limit=limit,
            offset=offset,
        )

        return {
            "talks": talks,
            "total": total,
            "applied_filters": {
                "query": q,
                "talk_types": talk_types,
                "taxonomy_filters": parsed_filters,
                "pagination": {"limit": limit, "offset": offset},
            },
        }
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
