import httpx
from typing import List, Optional
from app.api.models import SearchResult, Author
from datetime import datetime, timedelta
import re


class BioRxivService:
    """
    bioRxiv and medRxiv preprint repository API integration.
    
    API Documentation: https://api.biorxiv.org/
    - Base URL: https://api.biorxiv.org/details/{server}/{interval}/{cursor}
    - No authentication required
    - Pagination: 100 results per call
    - Note: API is date-based, not keyword-based - requires client-side filtering
    
    bioRxiv: Life sciences preprints
    medRxiv: Medical and health sciences preprints
    """
    
    BASE_URL = "https://api.biorxiv.org/details"
    
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
        Search bioRxiv and medRxiv for preprints.
        
        Note: The bioRxiv/medRxiv API doesn't support keyword search directly.
        We fetch recent preprints and filter client-side by matching the query
        against title and abstract.
        
        Args:
            query: Search query string (used for client-side filtering)
            page: Page number (1-indexed)
            per_page: Results per page
            year_min: Minimum publication year filter
            year_max: Maximum publication year filter
        
        Returns:
            Tuple of (list of SearchResult, total count)
        """
        
        # Calculate date range - fetch last 60 days of preprints for filtering
        end_date = datetime.now()
        start_date = end_date - timedelta(days=60)
        
        # Apply year filters if specified
        if year_min:
            filter_start = datetime(year_min, 1, 1)
            if filter_start > start_date:
                start_date = filter_start
        if year_max:
            filter_end = datetime(year_max, 12, 31)
            if filter_end < end_date:
                end_date = filter_end
        
        interval = f"{start_date.strftime('%Y-%m-%d')}/{end_date.strftime('%Y-%m-%d')}"
        
        # Search both bioRxiv and medRxiv
        all_results = []
        
        for server in ["biorxiv", "medrxiv"]:
            server_results = await self._fetch_and_filter(
                server=server,
                interval=interval,
                query=query,
                year_min=year_min,
                year_max=year_max
            )
            all_results.extend(server_results)
        
        # Sort by relevance (simple scoring based on query match)
        all_results = self._sort_by_relevance(all_results, query)
        
        # Apply pagination
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        paginated_results = all_results[start_idx:end_idx]
        
        return paginated_results, len(all_results)
    
    async def _fetch_and_filter(
        self,
        server: str,
        interval: str,
        query: str,
        year_min: Optional[int] = None,
        year_max: Optional[int] = None,
        max_fetch: int = 500
    ) -> List[SearchResult]:
        """Fetch preprints from a server and filter by query."""
        
        results = []
        cursor = 0
        query_lower = query.lower()
        query_words = set(query_lower.split())
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                while cursor < max_fetch:
                    url = f"{self.BASE_URL}/{server}/{interval}/{cursor}"
                    
                    response = await client.get(url)
                    response.raise_for_status()
                    data = response.json()
                    
                    collection = data.get("collection", [])
                    if not collection:
                        break
                    
                    for item in collection:
                        # Filter by query match in title or abstract
                        if self._matches_query(item, query_lower, query_words):
                            result = self._parse_preprint(item, server)
                            if result:
                                # Apply year filters
                                if year_min and result.publication_year and result.publication_year < year_min:
                                    continue
                                if year_max and result.publication_year and result.publication_year > year_max:
                                    continue
                                results.append(result)
                    
                    # Move to next batch
                    cursor += 100
                    
                    # Stop if we have enough results
                    if len(results) >= max_fetch:
                        break
                    
                    # Check if more results available
                    messages = data.get("messages", [])
                    if messages:
                        total_str = messages[0].get("total", "0")
                        try:
                            total = int(total_str)
                            if cursor >= total:
                                break
                        except ValueError:
                            pass
                
        except httpx.HTTPError as e:
            print(f"{server} HTTP error: {e}")
        except Exception as e:
            print(f"{server} error: {type(e).__name__}: {e}")
        
        return results
    
    def _matches_query(self, item: dict, query_lower: str, query_words: set) -> bool:
        """Check if item matches the search query."""
        title = (item.get("title") or "").lower()
        abstract = (item.get("abstract") or "").lower()
        
        # Check if any query word appears in title or abstract
        text = f"{title} {abstract}"
        
        # Require at least half the query words to match
        matches = sum(1 for word in query_words if word in text)
        return matches >= max(1, len(query_words) // 2)
    
    def _sort_by_relevance(self, results: List[SearchResult], query: str) -> List[SearchResult]:
        """Sort results by simple relevance score."""
        query_words = set(query.lower().split())
        
        def score(result: SearchResult) -> float:
            title_lower = (result.title or "").lower()
            abstract_lower = (result.abstract or "").lower()
            
            score = 0.0
            for word in query_words:
                if word in title_lower:
                    score += 2.0  # Title match worth more
                if word in abstract_lower:
                    score += 1.0
            
            # Boost recent publications
            if result.publication_year:
                if result.publication_year >= 2024:
                    score += 1.0
                elif result.publication_year >= 2023:
                    score += 0.5
            
            return score
        
        return sorted(results, key=score, reverse=True)
    
    def _parse_preprint(self, item: dict, server: str) -> Optional[SearchResult]:
        """Parse bioRxiv/medRxiv item into SearchResult model."""
        try:
            # Extract DOI
            doi = item.get("doi", "")
            
            # Extract title
            title = item.get("title", "Untitled")
            if title:
                title = title.strip()
            
            # Extract abstract
            abstract = item.get("abstract")
            if abstract:
                abstract = abstract.strip()
                if len(abstract) > 500:
                    abstract = abstract[:500] + "..."
            
            # Extract authors (semicolon-separated string)
            authors_str = item.get("authors", "")
            authors = []
            if authors_str:
                for author_name in authors_str.split(";")[:5]:
                    name = author_name.strip()
                    if name:
                        authors.append(Author(name=name))
            
            if not authors:
                authors.append(Author(name="Unknown Author"))
            
            # Extract publication date
            date_str = item.get("date")
            year = None
            if date_str:
                try:
                    date = datetime.strptime(date_str, "%Y-%m-%d")
                    year = date.year
                except ValueError:
                    pass
            
            # Get version
            version = item.get("version", "1")
            
            # Construct URLs
            # Abstract page: https://www.biorxiv.org/content/{doi}
            # PDF: https://www.biorxiv.org/content/{doi}v{version}.full.pdf
            base_domain = "www.biorxiv.org" if server == "biorxiv" else "www.medrxiv.org"
            
            url = f"https://{base_domain}/content/{doi}"
            pdf_url = f"https://{base_domain}/content/{doi}v{version}.full.pdf"
            
            # Determine source name
            source = "bioRxiv" if server == "biorxiv" else "medRxiv"
            
            return SearchResult(
                id=f"{server}:{doi}" if doi else "unknown",
                title=title,
                authors=authors,
                abstract=abstract,
                publication_year=year,
                source=source,
                doi=doi,
                url=url,
                is_open_access=True,  # All preprints are open access
                open_access_url=pdf_url,
                cited_by_count=0,  # API doesn't provide citation counts
                relevance_score=0.0
            )
            
        except Exception as e:
            print(f"Error parsing {server} preprint: {type(e).__name__}: {e}")
            return None
