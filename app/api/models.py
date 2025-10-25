from pydantic import BaseModel
from typing import List, Optional
from datetime import date

class Author(BaseModel):
    name: str
    affiliation: Optional[str] = None

class SearchResult(BaseModel):
    id: str
    title: str
    authors: List[Author]
    abstract: Optional[str] = None
    publication_year: Optional[int] = None
    source: str  # "OpenAlex", "CrossRef", etc.
    doi: Optional[str] = None
    url: Optional[str] = None
    is_open_access: bool = False
    open_access_url: Optional[str] = None
    cited_by_count: Optional[int] = 0
    relevance_score: float = 0.0

class SearchResponse(BaseModel):
    query: str
    total_results: int
    results: List[SearchResult]
    search_time: float
    databases_searched: List[str]

class SearchRequest(BaseModel):
    query: str
    page: int = 1
    per_page: int = 20
    year_min: Optional[int] = None
    year_max: Optional[int] = None
    open_access_only: bool = False