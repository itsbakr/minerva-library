import httpx
from typing import List, Optional
from app.api.models import SearchResult, Author
import re

class CrossRefService:
    BASE_URL = "https://api.crossref.org"
    
    async def search(
        self,
        query: str,
        page: int = 1,
        per_page: int = 20,
        year_min: Optional[int] = None,
        year_max: Optional[int] = None
    ) -> tuple[List[SearchResult], int]:
        """Search CrossRef for scholarly works"""
        
        # Build filters
        filters = []
        if year_min:
            filters.append(f"from-pub-date:{year_min}")
        if year_max:
            filters.append(f"until-pub-date:{year_max}")
        
        filter_string = ",".join(filters) if filters else None
        
        # Calculate offset for pagination
        offset = (page - 1) * per_page
        
        params = {
            "query": query,
            "rows": per_page,
            "offset": offset,
            "mailto": "library@minerva.edu"
        }
        if filter_string:
            params["filter"] = filter_string
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self.BASE_URL}/works",
                    params=params
                )
                response.raise_for_status()
                data = response.json()
                
                # Parse results
                results = []
                items = data.get("message", {}).get("items", [])
                for item in items:
                    result = self._parse_work(item)
                    if result:
                        results.append(result)
                
                total_count = data.get("message", {}).get("total-results", 0)
                return results, total_count
                
        except httpx.HTTPError as e:
            print(f"CrossRef HTTP error: {e}")
            return [], 0
        except Exception as e:
            print(f"CrossRef error: {type(e).__name__}: {e}")
            return [], 0
    def _clean_html(self, text: str) -> str:
        """Remove HTML tags from text"""
        if not text:
            return text
        # Remove HTML tags
        clean = re.sub(r'<[^>]+>', '', text)
        # Remove extra whitespace
        clean = ' '.join(clean.split())
        return clean

    def _parse_work(self, work: dict) -> Optional[SearchResult]:
        """Parse CrossRef work into SearchResult model"""
        try:
            # Extract authors
            authors = []
            for author in work.get("author", [])[:5]:
                given = author.get("given", "")
                family = author.get("family", "")
                name = f"{given} {family}".strip()
                if name:
                    authors.append(Author(name=name))
            
            # If no authors, add placeholder
            if not authors:
                authors.append(Author(name="Unknown Author"))
            
            # Extract publication year
            year = None
            pub_date = work.get("published-print") or work.get("published-online") or work.get("created")
            if pub_date and "date-parts" in pub_date:
                try:
                    year = pub_date["date-parts"][0][0]
                except (IndexError, TypeError):
                    pass
            
            # Extract title
            titles = work.get("title", [])
            title = titles[0] if titles else "Untitled"
            
            # Extract abstract
            abstract = self._clean_html(work.get("abstract"))
            if abstract and len(abstract) > 500:
                abstract = abstract[:500] + "..."
            
            # Get DOI
            doi = work.get("DOI")
            
            return SearchResult(
                id=doi or "unknown",
                title=title,
                authors=authors,
                abstract=abstract,
                publication_year=year,
                source="CrossRef",
                doi=doi,
                url=f"https://doi.org/{doi}" if doi else None,
                is_open_access=False,
                open_access_url=None,
                cited_by_count=work.get("is-referenced-by-count", 0),
                relevance_score=0.0
            )
        except Exception as e:
            print(f"Error parsing CrossRef work: {type(e).__name__}: {e}")
            print(f"Work data: {work}")
            return None