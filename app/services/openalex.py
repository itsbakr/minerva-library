import httpx
from typing import List, Optional
from app.api.models import SearchResult, Author

class OpenAlexService:
    BASE_URL = "https://api.openalex.org"
    
    async def search(
        self,
        query: str,
        page: int = 1,
        per_page: int = 20,
        year_min: Optional[int] = None,
        year_max: Optional[int] = None,
        open_access_only: bool = False
    ) -> tuple[List[SearchResult], int]:
        """Search OpenAlex for scholarly works"""
        
        # Build filters
        filters = []
        if year_min and year_max:
            filters.append(f"publication_year:{year_min}-{year_max}")
        elif year_min:
            filters.append(f"publication_year:>{year_min}")
        elif year_max:
            filters.append(f"publication_year:<{year_max}")
            
        if open_access_only:
            filters.append("is_oa:true")
        
        filter_string = ",".join(filters) if filters else None
        
        # Make API request with proper async client
        params = {
            "search": query,
            "page": page,
            "per_page": per_page,
        }
        if filter_string:
            params["filter"] = filter_string
        
        try:
            # Use async context manager for client
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self.BASE_URL}/works",
                    params=params
                )
                response.raise_for_status()
                data = response.json()
                
                # Parse results
                results = []
                for item in data.get("results", []):
                    result = self._parse_work(item)
                    if result:
                        results.append(result)
                
                total_count = data.get("meta", {}).get("count", 0)
                return results, total_count
                
        except httpx.HTTPError as e:
            print(f"OpenAlex HTTP error: {e}")
            return [], 0
        except Exception as e:
            print(f"OpenAlex error: {type(e).__name__}: {e}")
            return [], 0
    
    def _parse_work(self, work: dict) -> Optional[SearchResult]:
        """Parse OpenAlex work into SearchResult model"""
        try:
            # Extract authors
            authors = []
            for authorship in work.get("authorships", [])[:5]:
                author_data = authorship.get("author", {})
                if author_data:
                    authors.append(Author(
                        name=author_data.get("display_name", "Unknown Author")
                    ))
            
            # If no authors, add placeholder
            if not authors:
                authors.append(Author(name="Unknown Author"))
            
            # Extract abstract
            abstract = self._extract_abstract(work.get("abstract_inverted_index"))
            
            # Extract open access info
            oa_info = work.get("open_access", {}) or {}
            is_oa = oa_info.get("is_oa", False)
            oa_url = oa_info.get("oa_url")
            
            # Get DOI
            doi = work.get("doi", "")
            if doi and doi.startswith("https://doi.org/"):
                doi = doi.replace("https://doi.org/", "")
            
            # Create result
            return SearchResult(
                id=work.get("id", "unknown"),
                title=work.get("title") or "Untitled",
                authors=authors,
                abstract=abstract,
                publication_year=work.get("publication_year"),
                source="OpenAlex",
                doi=doi if doi else None,
                url=work.get("doi") or work.get("id"),
                is_open_access=is_oa,
                open_access_url=oa_url,
                cited_by_count=work.get("cited_by_count", 0),
                relevance_score=0.0
            )
        except Exception as e:
            print(f"Error parsing OpenAlex work: {type(e).__name__}: {e}")
            print(f"Work data: {work}")
            return None
    
    def _extract_abstract(self, inverted_index: Optional[dict]) -> Optional[str]:
        """Convert OpenAlex's inverted index to readable abstract"""
        if not inverted_index:
            return None
        
        try:
            # Reconstruct text from inverted index
            words = {}
            for word, positions in inverted_index.items():
                for pos in positions:
                    words[pos] = word
            
            # Sort by position and join
            if not words:
                return None
                
            sorted_words = [words[i] for i in sorted(words.keys())]
            abstract = " ".join(sorted_words)
            
            # Limit length
            if len(abstract) > 500:
                abstract = abstract[:500] + "..."
            
            return abstract
        except Exception as e:
            print(f"Error extracting abstract: {e}")
            return None