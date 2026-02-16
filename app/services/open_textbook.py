import httpx
from typing import List, Optional
from app.api.models import SearchResult, Author


class OpenTextbookService:
    """
    Open Textbook Library API integration.
    
    API Documentation: https://open.umn.edu/opentextbooks/api-docs/index.html
    - Base URL: https://open.umn.edu/opentextbooks
    - No authentication required
    - Returns JSON, CSV, or RSS
    - Free, peer-reviewed textbooks
    """
    
    BASE_URL = "https://open.umn.edu/opentextbooks"
    
    # Cache for textbooks (small dataset, can cache all)
    _cache: Optional[List[dict]] = None
    _cache_timestamp: Optional[float] = None
    CACHE_TTL = 3600  # 1 hour
    
    async def search(
        self,
        query: str,
        page: int = 1,
        per_page: int = 20,
        year_min: Optional[int] = None,
        year_max: Optional[int] = None,
        **kwargs
    ) -> tuple[List[SearchResult], int]:
        """
        Search Open Textbook Library for free textbooks.
        
        Note: The API returns all textbooks, so we filter client-side.
        The dataset is small enough to cache and search locally.
        
        Args:
            query: Search query string
            page: Page number (1-indexed)
            per_page: Results per page
            year_min: Minimum publication year filter
            year_max: Maximum publication year filter
        
        Returns:
            Tuple of (list of SearchResult, total count)
        """
        
        # Fetch all textbooks (with caching)
        all_textbooks = await self._fetch_all_textbooks()
        
        if not all_textbooks:
            return [], 0
        
        # Filter by query
        query_lower = query.lower()
        query_words = set(query_lower.split())
        
        filtered = []
        for textbook in all_textbooks:
            if self._matches_query(textbook, query_lower, query_words):
                result = self._parse_textbook(textbook)
                if result:
                    # Apply year filters
                    if year_min and result.publication_year and result.publication_year < year_min:
                        continue
                    if year_max and result.publication_year and result.publication_year > year_max:
                        continue
                    filtered.append(result)
        
        # Sort by relevance
        filtered = self._sort_by_relevance(filtered, query)
        
        # Apply pagination
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        paginated = filtered[start_idx:end_idx]
        
        return paginated, len(filtered)
    
    async def _fetch_all_textbooks(self) -> List[dict]:
        """Fetch all textbooks from the API (with caching)."""
        import time
        
        # Check cache
        if self._cache is not None and self._cache_timestamp is not None:
            if time.time() - self._cache_timestamp < self.CACHE_TTL:
                return self._cache
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self.BASE_URL}/textbooks.json"
                )
                response.raise_for_status()
                data = response.json()
                
                # Cache the results
                if isinstance(data, dict):
                    textbooks = data.get("data", [])
                elif isinstance(data, list):
                    textbooks = data
                else:
                    textbooks = []
                
                self._cache = textbooks
                self._cache_timestamp = time.time()
                
                return textbooks
                
        except httpx.HTTPError as e:
            print(f"Open Textbook Library HTTP error: {e}")
            return self._cache or []
        except Exception as e:
            print(f"Open Textbook Library error: {type(e).__name__}: {e}")
            return self._cache or []
    
    def _matches_query(self, textbook: dict, query_lower: str, query_words: set) -> bool:
        """Check if textbook matches the search query."""
        title = (textbook.get("title") or "").lower()
        description = (textbook.get("description") or "").lower()
        subjects = " ".join([s.get("name", "") for s in textbook.get("subjects", [])]).lower()
        
        text = f"{title} {description} {subjects}"
        
        # Require at least one query word to match
        for word in query_words:
            if len(word) > 2 and word in text:  # Skip very short words
                return True
        
        return False
    
    def _sort_by_relevance(self, results: List[SearchResult], query: str) -> List[SearchResult]:
        """Sort results by relevance score."""
        query_words = set(query.lower().split())
        
        def score(result: SearchResult) -> float:
            title_lower = (result.title or "").lower()
            abstract_lower = (result.abstract or "").lower()
            
            score = 0.0
            for word in query_words:
                if len(word) > 2:  # Skip short words
                    if word in title_lower:
                        score += 3.0  # Title match worth more
                    if word in abstract_lower:
                        score += 1.0
            
            return score
        
        return sorted(results, key=score, reverse=True)
    
    def _parse_textbook(self, textbook: dict) -> Optional[SearchResult]:
        """Parse textbook data into SearchResult model."""
        try:
            # Extract ID
            textbook_id = textbook.get("id", "unknown")
            
            # Extract title
            title = textbook.get("title", "Untitled")
            
            # Extract description as abstract
            abstract = textbook.get("description")
            if abstract and len(abstract) > 500:
                abstract = abstract[:500] + "..."
            
            # Extract authors/contributors
            authors = []
            contributors = textbook.get("contributors", [])
            if isinstance(contributors, list):
                for contributor in contributors[:5]:
                    if isinstance(contributor, dict):
                        name = contributor.get("name", "")
                    else:
                        name = str(contributor)
                    if name:
                        authors.append(Author(name=name))
            
            # Also check for author field
            if not authors:
                author_str = textbook.get("author") or textbook.get("authors")
                if author_str:
                    if isinstance(author_str, list):
                        for name in author_str[:5]:
                            if name:
                                authors.append(Author(name=str(name)))
                    elif isinstance(author_str, str):
                        authors.append(Author(name=author_str))
            
            if not authors:
                authors.append(Author(name="Unknown Author"))
            
            # Extract publication year
            year = None
            date_str = textbook.get("copyright_year") or textbook.get("last_updated")
            if date_str:
                try:
                    year = int(str(date_str)[:4])
                except (ValueError, TypeError):
                    pass
            
            # Extract URLs
            url = textbook.get("url") or f"{self.BASE_URL}/textbooks/{textbook_id}"
            open_access_url = textbook.get("pdf_url") or textbook.get("link")
            
            # If no direct link, use the main URL
            if not open_access_url:
                open_access_url = url
            
            return SearchResult(
                id=f"otl:{textbook_id}",
                title=title,
                authors=authors,
                abstract=abstract,
                publication_year=year,
                source="Open Textbook Library",
                doi=None,  # Textbooks typically don't have DOIs
                url=url,
                is_open_access=True,  # All textbooks in the library are open access
                open_access_url=open_access_url,
                cited_by_count=0,
                relevance_score=0.0
            )
            
        except Exception as e:
            print(f"Error parsing textbook: {type(e).__name__}: {e}")
            return None
