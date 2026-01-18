from fastapi import APIRouter, Query, HTTPException, Request
from typing import Optional
from app.api.models import SearchResponse
from app.services.aggregator import SearchAggregator
from app.database import AsyncSessionLocal, SearchHistory
import time
import traceback
from sqlalchemy import select, func

router = APIRouter(prefix="/api", tags=["search"])

@router.get("/search", response_model=SearchResponse)
async def search(
    request: Request,
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
        results, total_count, databases, provider_status = await aggregator.search_all(
            query=q,
            page=page,
            per_page=per_page,
            year_min=year_min,
            year_max=year_max,
            open_access_only=open_access_only
        )
        
        search_time = time.time() - start_time
        
        # Log search to database
        try:
            import json
            async with AsyncSessionLocal() as session:
                search_record = SearchHistory(
                    query=q,
                    filters=json.dumps({
                        "year_min": year_min,
                        "year_max": year_max,
                        "open_access_only": open_access_only,
                        "page": page,
                        "per_page": per_page
                    }),
                    results_count=total_count,
                    search_time=round(search_time, 2),
                    databases_searched=json.dumps(databases) if databases else None,
                    user_ip=request.client.host if request.client else None
                )
                session.add(search_record)
                await session.commit()
        except Exception as e:
            print(f"Failed to log search: {e}")
            # Don't fail the request if logging fails
        
        return SearchResponse(
            query=q,
            total_results=total_count,
            results=results,
            search_time=round(search_time, 2),
            databases_searched=databases if databases else ["None"],
            provider_status=provider_status  # new detailed status
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

@router.get("/search/history")
async def get_search_history(
    limit: int = Query(20, ge=1, le=100, description="Number of recent searches")
):
    """Get recent search history"""
    
    try:
        import json
        async with AsyncSessionLocal() as session:
            query = select(SearchHistory).order_by(
                SearchHistory.created_at.desc()
            ).limit(limit)
            
            result = await session.execute(query)
            results = result.scalars().all()
            
            return {
                "count": len(results),
                "searches": [
                    {
                        "query": row.query,
                        "results_count": row.results_count,
                        "search_time": row.search_time,
                        "databases": json.loads(row.databases_searched) if row.databases_searched else [],
                        "timestamp": row.created_at.isoformat() if row.created_at else None
                    }
                    for row in results
                ]
            }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch history: {str(e)}"
        )

@router.get("/search/stats")
async def get_search_stats():
    """Get search statistics"""
    
    try:
        async with AsyncSessionLocal() as session:
            # Total searches
            total_query = select(func.count()).select_from(SearchHistory)
            total_result = await session.execute(total_query)
            total_searches = total_result.scalar() or 0
            
            # Average search time
            avg_time_query = select(func.avg(SearchHistory.search_time))
            avg_result = await session.execute(avg_time_query)
            avg_search_time = avg_result.scalar() or 0.0
            
            # Most common queries
            all_searches_query = select(SearchHistory.query)
            all_result = await session.execute(all_searches_query)
            all_searches = all_result.scalars().all()
            
            # Count queries in Python
            query_counts = {}
            for query in all_searches:
                query_counts[query] = query_counts.get(query, 0) + 1
            
            # Sort and get top 10
            common_queries = sorted(
                query_counts.items(),
                key=lambda x: x[1],
                reverse=True
            )[:10]
            
            return {
                "total_searches": total_searches,
                "average_search_time": round(avg_search_time, 2),
                "most_common_queries": [
                    {"query": query, "count": count}
                    for query, count in common_queries
                ]
            }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch stats: {str(e)}"
        )