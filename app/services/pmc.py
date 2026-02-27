import httpx
from typing import List, Optional
from app.api.models import SearchResult, Author
import xml.etree.ElementTree as ET
import re


class PMCService:
    """
    PubMed Central (PMC) Open Access API integration.
    
    API Documentation: https://www.ncbi.nlm.nih.gov/pmc/tools/developers/
    
    Uses NCBI E-utilities for search and PMC ID lookup:
    - ESearch: Search and retrieve PMC IDs
    - ESummary: Get article summaries
    
    PMC contains 8+ million full-text articles in biomedical and life sciences.
    The Open Access subset contains articles with permissive licenses.
    """
    
    ESEARCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
    ESUMMARY_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
    
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
        Search PubMed Central for open access articles.
        
        Args:
            query: Search query string
            page: Page number (1-indexed)
            per_page: Results per page (max 100)
            year_min: Minimum publication year filter
            year_max: Maximum publication year filter
        
        Returns:
            Tuple of (list of SearchResult, total count)
        """
        
        # Build PMC search query with year filters
        search_query = query
        
        if year_min and year_max:
            search_query += f" AND {year_min}:{year_max}[pdat]"
        elif year_min:
            search_query += f" AND {year_min}:3000[pdat]"
        elif year_max:
            search_query += f" AND 1900:{year_max}[pdat]"
        
        # Add open access filter
        search_query += " AND open access[filter]"
        
        # Calculate retstart for pagination
        retstart = (page - 1) * per_page
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Step 1: Search to get PMC IDs
                search_params = {
                    "db": "pmc",
                    "term": search_query,
                    "retstart": retstart,
                    "retmax": min(per_page, 100),
                    "retmode": "json",
                    "sort": "relevance",
                    "tool": "minerva-library",
                    "email": "library@minerva.edu"
                }
                
                search_response = await client.get(
                    self.ESEARCH_URL,
                    params=search_params
                )
                search_response.raise_for_status()
                search_data = search_response.json()
                
                esearch_result = search_data.get("esearchresult", {})
                pmc_ids = esearch_result.get("idlist", [])
                total_count = int(esearch_result.get("count", 0))
                
                if not pmc_ids:
                    return [], total_count
                
                # Step 2: Get article summaries
                summary_params = {
                    "db": "pmc",
                    "id": ",".join(pmc_ids),
                    "retmode": "json",
                    "tool": "minerva-library",
                    "email": "library@minerva.edu"
                }
                
                summary_response = await client.get(
                    self.ESUMMARY_URL,
                    params=summary_params
                )
                summary_response.raise_for_status()
                summary_data = summary_response.json()
                
                # Parse results
                results = []
                result_dict = summary_data.get("result", {})
                
                for pmc_id in pmc_ids:
                    article_data = result_dict.get(pmc_id)
                    if article_data:
                        result = self._parse_article(article_data, pmc_id)
                        if result:
                            results.append(result)
                
                return results, total_count
                
        except httpx.HTTPError as e:
            print(f"PMC HTTP error: {e}")
            return [], 0
        except Exception as e:
            print(f"PMC error: {type(e).__name__}: {e}")
            return [], 0
    
    def _parse_article(self, article: dict, pmc_id: str) -> Optional[SearchResult]:
        """Parse PMC article summary into SearchResult model."""
        try:
            # Extract title
            title = article.get("title", "Untitled")
            # Clean HTML from title
            title = re.sub(r'<[^>]+>', '', title)
            
            # Extract authors
            authors = []
            author_list = article.get("authors", [])
            if isinstance(author_list, list):
                for author in author_list[:5]:
                    if isinstance(author, dict):
                        name = author.get("name", "")
                    else:
                        name = str(author)
                    if name:
                        authors.append(Author(name=name))
            
            if not authors:
                authors.append(Author(name="Unknown Author"))
            
            # Extract publication year
            year = None
            pub_date = article.get("pubdate", "") or article.get("epubdate", "")
            if pub_date:
                try:
                    year = int(pub_date[:4])
                except (ValueError, TypeError):
                    pass
            
            # Extract DOI
            doi = None
            article_ids = article.get("articleids", [])
            if isinstance(article_ids, list):
                for aid in article_ids:
                    if isinstance(aid, dict) and aid.get("idtype") == "doi":
                        doi = aid.get("value")
                        break
            
            # Build URLs
            # PMC article URL: https://www.ncbi.nlm.nih.gov/pmc/articles/PMC{id}/
            url = f"https://www.ncbi.nlm.nih.gov/pmc/articles/PMC{pmc_id}/"
            
            # PDF URL: https://www.ncbi.nlm.nih.gov/pmc/articles/PMC{id}/pdf/
            pdf_url = f"https://www.ncbi.nlm.nih.gov/pmc/articles/PMC{pmc_id}/pdf/"
            
            # Use DOI URL if available
            if doi:
                url = f"https://doi.org/{doi}"
            
            # Extract source/journal
            source = article.get("fulljournalname") or article.get("source", "PMC")
            
            return SearchResult(
                id=f"PMC{pmc_id}",
                title=title,
                authors=authors,
                abstract=None,  # ESummary doesn't return abstracts; would need EFetch
                publication_year=year,
                source="PMC",
                doi=doi,
                url=url,
                is_open_access=True,  # We filter for OA in search
                open_access_url=pdf_url,
                cited_by_count=0,  # Would need separate citation lookup
                relevance_score=0.0
            )
            
        except Exception as e:
            print(f"Error parsing PMC article {pmc_id}: {type(e).__name__}: {e}")
            return None
