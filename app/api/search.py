from fastapi import APIRouter, Query, HTTPException
from typing import Optional
from app.api.models import SearchResponse
from app.services.aggregator import SearchAggregator
import time
import traceback

router = APIRouter(prefix="/api", tags=["search"])

@router.get("/search", response_model=SearchResponse)
async def search(
    q: str = Query(..., description="Search query", min_length=1),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Results per page"),
    year_min: Optional[int] = Query(None, ge=1900, le=2025, description="Minimum publication year"),
    year_max: Optional[int] = Query(None, ge=1900, le=2025, description="Maximum publication year"),
    open_access_only: bool = Query(False, description="Return only open access articles")
):
    """
    Search across all academic databases
    
    Example: /api/search?q=climate+change+agriculture&year_min=2020
    """
    
    try:
        start_time = time.time()
        
        # Create aggregator
        aggregator = SearchAggregator()
        
        # Perform search
        results, total_count, databases = await aggregator.search_all(
            query=q,
            page=page,
            per_page=per_page,
            year_min=year_min,
            year_max=year_max,
            open_access_only=open_access_only
        )
        
        search_time = time.time() - start_time
        
        return SearchResponse(
            query=q,
            total_results=total_count,
            results=results,
            search_time=round(search_time, 2),
            databases_searched=databases if databases else ["None"]
        )
        
    except Exception as e:
        # Print full traceback for debugging
        print(f"ERROR in search endpoint:")
        print(traceback.format_exc())
        
        # Return user-friendly error
        raise HTTPException(
            status_code=500,
            detail=f"Search failed: {str(e)}"
        )