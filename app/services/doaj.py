import httpx
from typing import List, Optional
from app.api.models import SearchResult, Author


class DOAJService:
    """
    Directory of Open Access Journals (DOAJ) API integration.
    
    API Documentation: https://doaj.org/docs/api/
    - Base URL: https://doaj.org/api/v4/search/articles
    - No authentication required for search
    - Rate limit: 2 requests per second
    - All results are open access by definition
    """
    
    BASE_URL = "https://doaj.org/api/search/articles"
    
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
        Search DOAJ for open access articles.
        
        Args:
            query: Search query string
            page: Page number (1-indexed)
            per_page: Results per page (max 100)
            year_min: Minimum publication year filter
            year_max: Maximum publication year filter
        
        Returns:
            Tuple of (list of SearchResult, total count)
        """
        
        # Build the query with optional year filters
        search_query = query
        
        # DOAJ uses Elasticsearch-style query syntax
        # Add year filters if specified
        filters = []
        if year_min and year_max:
            filters.append(f"bibjson.year:[{year_min} TO {year_max}]")
        elif year_min:
            filters.append(f"bibjson.year:[{year_min} TO *]")
        elif year_max:
            filters.append(f"bibjson.year:[* TO {year_max}]")
        
        if filters:
            search_query = f"({query}) AND {' AND '.join(filters)}"
        
        params = {
            "q": search_query,
            "page": page,
            "pageSize": min(per_page, 100),  # DOAJ max is 100
        }
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    self.BASE_URL,
                    params=params
                )
                response.raise_for_status()
                data = response.json()
                
                # Parse results
                results = []
                items = data.get("results", [])
                for item in items:
                    result = self._parse_article(item)
                    if result:
                        results.append(result)
                
                total_count = data.get("total", 0)
                return results, total_count
                
        except httpx.HTTPError as e:
            print(f"DOAJ HTTP error: {e}")
            return [], 0
        except Exception as e:
            print(f"DOAJ error: {type(e).__name__}: {e}")
            return [], 0
    
    def _parse_article(self, article: dict) -> Optional[SearchResult]:
        """Parse DOAJ article into SearchResult model."""
        try:
            bibjson = article.get("bibjson", {})
            
            # Extract title
            title = bibjson.get("title", "Untitled")
            
            # Extract authors
            authors = []
            for author in bibjson.get("author", [])[:5]:
                name = author.get("name", "")
                if name:
                    authors.append(Author(name=name))
            
            if not authors:
                authors.append(Author(name="Unknown Author"))
            
            # Extract abstract
            abstract = bibjson.get("abstract")
            if abstract and len(abstract) > 500:
                abstract = abstract[:500] + "..."
            
            # Extract publication year
            year = None
            year_str = bibjson.get("year")
            if year_str:
                try:
                    year = int(year_str)
                except (ValueError, TypeError):
                    pass
            
            # Extract DOI from identifiers
            doi = None
            for identifier in bibjson.get("identifier", []):
                if identifier.get("type") == "doi":
                    doi = identifier.get("id")
                    break
            
            # Extract full-text URL (open access link)
            open_access_url = None
            for link in bibjson.get("link", []):
                if link.get("type") == "fulltext":
                    open_access_url = link.get("url")
                    break
            
            # Fallback to any available link
            if not open_access_url:
                links = bibjson.get("link", [])
                if links:
                    open_access_url = links[0].get("url")
            
            # Build article ID
            article_id = article.get("id", doi or "unknown")
            
            # URL - prefer DOI link, fallback to OA URL
            url = f"https://doi.org/{doi}" if doi else open_access_url
            
            return SearchResult(
                id=article_id,
                title=title,
                authors=authors,
                abstract=abstract,
                publication_year=year,
                source="DOAJ",
                doi=doi,
                url=url,
                is_open_access=True,  # All DOAJ articles are open access
                open_access_url=open_access_url,
                cited_by_count=0,  # DOAJ doesn't provide citation counts
                relevance_score=0.0
            )
            
        except Exception as e:
            print(f"Error parsing DOAJ article: {type(e).__name__}: {e}")
            return None
