import httpx
from typing import List, Optional, Dict
from app.api.models import SearchResult, Author
import asyncio

class UnpaywallService:
    """
    Unpaywall API for finding open access versions of articles
    Free API, no authentication needed, just email
    """
    BASE_URL = "https://api.unpaywall.org/v2"
    EMAIL = "library@minerva.edu"  # Required for polite pool
    
    async def search(
        self,
        query: str,
        page: int = 1,
        per_page: int = 20,
        **filters
    ) -> tuple[List[SearchResult], int]:
        """
        Search Unpaywall by title
        Note: Unpaywall's search is basic, mainly used for DOI lookups
        """
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self.BASE_URL}/search/",
                    params={
                        "query": query,
                        "is_oa": "true",  # Only open access
                        "email": self.EMAIL
                    }
                )
                response.raise_for_status()
                data = response.json()
                
                results = []
                items = data.get("results", [])
                
                for item in items[:per_page]:
                    result = self._parse_article(item)
                    if result:
                        results.append(result)
                
                return results, len(results)
                
        except httpx.HTTPError as e:
            print(f"Unpaywall HTTP error: {e}")
            return [], 0
        except Exception as e:
            print(f"Unpaywall error: {type(e).__name__}: {e}")
            return [], 0
    
    async def enrich_with_oa(self, results: List[SearchResult]) -> List[SearchResult]:
        """
        Enrich existing results with open access information from Unpaywall
        This is the main use case - checking DOIs for OA availability
        """
        
        # Filter results that have DOIs but no OA info yet
        results_to_check = [
            r for r in results 
            if r.doi and not r.is_open_access
        ]
        
        if not results_to_check:
            return results
        
        # Check DOIs in parallel (but respect rate limits)
        tasks = [
            self._check_doi_oa(result.doi)
            for result in results_to_check
        ]
        
        # Limit concurrent requests to avoid rate limiting
        oa_info_list = []
        for i in range(0, len(tasks), 10):  # Process 10 at a time
            batch = tasks[i:i+10]
            batch_results = await asyncio.gather(*batch, return_exceptions=True)
            oa_info_list.extend(batch_results)
            await asyncio.sleep(0.1)  # Small delay between batches
        
        # Create lookup dict
        doi_to_oa = {}
        for result, oa_info in zip(results_to_check, oa_info_list):
            if oa_info and not isinstance(oa_info, Exception):
                doi_to_oa[result.doi] = oa_info
        
        # Update results with OA information
        enriched_results = []
        for result in results:
            if result.doi in doi_to_oa:
                oa_info = doi_to_oa[result.doi]
                result.is_open_access = oa_info.get("is_oa", False)
                result.open_access_url = oa_info.get("oa_url")
            enriched_results.append(result)
        
        return enriched_results
    
    async def _check_doi_oa(self, doi: str) -> Optional[Dict]:
        """Check if a DOI has open access via Unpaywall"""
        
        if not doi:
            return None
        
        # Clean DOI (remove https://doi.org/ prefix if present)
        clean_doi = doi.replace("https://doi.org/", "").replace("http://dx.doi.org/", "").strip()
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{self.BASE_URL}/{clean_doi}",
                    params={"email": self.EMAIL}
                )
                
                if response.status_code == 404:
                    return None
                
                response.raise_for_status()
                data = response.json()
                
                best_oa = data.get("best_oa_location", {})
                
                return {
                    "is_oa": data.get("is_oa", False),
                    "oa_url": best_oa.get("url_for_pdf") or best_oa.get("url"),
                    "oa_status": data.get("oa_status"),
                    "version": best_oa.get("version")
                }
                
        except Exception as e:
            print(f"Error checking DOI {clean_doi}: {e}")
            return None
    
    def _parse_article(self, article: dict) -> Optional[SearchResult]:
        """Parse Unpaywall article into SearchResult"""
        
        try:
            # Extract authors
            authors = []
            for author in article.get("z_authors", [])[:5]:
                name = author.get("family", "")
                given = author.get("given", "")
                full_name = f"{given} {name}".strip()
                if full_name:
                    authors.append(Author(name=full_name))
            
            if not authors:
                authors.append(Author(name="Unknown Author"))
            
            # Get best OA location
            best_oa = article.get("best_oa_location", {}) or {}
            
            return SearchResult(
                id=article.get("doi", "unknown"),
                title=article.get("title", "Untitled"),
                authors=authors,
                abstract=None,  # Unpaywall doesn't provide abstracts
                publication_year=article.get("year"),
                source="Unpaywall",
                doi=article.get("doi"),
                url=best_oa.get("url") or f"https://doi.org/{article.get('doi')}",
                is_open_access=True,  # We filtered for OA only
                open_access_url=best_oa.get("url_for_pdf") or best_oa.get("url"),
                cited_by_count=0,  # Unpaywall doesn't provide citation counts
                relevance_score=0.0
            )
            
        except Exception as e:
            print(f"Error parsing Unpaywall article: {e}")
            return None

