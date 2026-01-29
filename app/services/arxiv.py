import httpx
from typing import List, Optional
from app.api.models import SearchResult, Author
import xml.etree.ElementTree as ET
from datetime import datetime
import re


class ArxivService:
    """
    arXiv preprint repository API integration.
    
    API Documentation: https://info.arxiv.org/help/api/user-manual.html
    - Base URL: http://export.arxiv.org/api/query
    - No authentication required
    - Rate limit: Max 1 request every 3 seconds
    - Returns Atom 1.0 XML format
    - Covers: physics, mathematics, computer science, quantitative biology,
              quantitative finance, statistics, electrical engineering, economics
    """
    
    BASE_URL = "http://export.arxiv.org/api/query"
    
    # Atom namespace
    ATOM_NS = "{http://www.w3.org/2005/Atom}"
    ARXIV_NS = "{http://arxiv.org/schemas/atom}"
    
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
        Search arXiv for preprints.
        
        Args:
            query: Search query string
            page: Page number (1-indexed)
            per_page: Results per page (max 100)
            year_min: Minimum publication year filter (applied client-side)
            year_max: Maximum publication year filter (applied client-side)
        
        Returns:
            Tuple of (list of SearchResult, total count)
        """
        
        # arXiv uses start index (0-based) instead of page number
        start = (page - 1) * per_page
        
        # Build arXiv query
        # arXiv supports field prefixes: all:, ti:, au:, abs:, cat:
        search_query = f"all:{query}"
        
        params = {
            "search_query": search_query,
            "start": start,
            "max_results": min(per_page, 100),
            "sortBy": "relevance",
            "sortOrder": "descending"
        }
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    self.BASE_URL,
                    params=params
                )
                response.raise_for_status()
                
                # Parse XML response
                root = ET.fromstring(response.text)
                
                # Extract total results count from opensearch namespace
                total_results_elem = root.find("{http://a9.com/-/spec/opensearch/1.1/}totalResults")
                total_count = int(total_results_elem.text) if total_results_elem is not None else 0
                
                # Parse entries
                results = []
                for entry in root.findall(f"{self.ATOM_NS}entry"):
                    result = self._parse_entry(entry, year_min, year_max)
                    if result:
                        results.append(result)
                
                return results, total_count
                
        except httpx.HTTPError as e:
            print(f"arXiv HTTP error: {e}")
            return [], 0
        except ET.ParseError as e:
            print(f"arXiv XML parse error: {e}")
            return [], 0
        except Exception as e:
            print(f"arXiv error: {type(e).__name__}: {e}")
            return [], 0
    
    def _parse_entry(
        self, 
        entry: ET.Element,
        year_min: Optional[int] = None,
        year_max: Optional[int] = None
    ) -> Optional[SearchResult]:
        """Parse arXiv Atom entry into SearchResult model."""
        try:
            # Extract arXiv ID from the entry ID URL
            # Format: http://arxiv.org/abs/2301.12345v1
            id_elem = entry.find(f"{self.ATOM_NS}id")
            arxiv_url = id_elem.text if id_elem is not None else ""
            arxiv_id = self._extract_arxiv_id(arxiv_url)
            
            # Extract title (remove newlines and extra spaces)
            title_elem = entry.find(f"{self.ATOM_NS}title")
            title = title_elem.text.strip() if title_elem is not None else "Untitled"
            title = " ".join(title.split())  # Normalize whitespace
            
            # Extract abstract/summary
            summary_elem = entry.find(f"{self.ATOM_NS}summary")
            abstract = summary_elem.text.strip() if summary_elem is not None else None
            if abstract:
                abstract = " ".join(abstract.split())  # Normalize whitespace
                if len(abstract) > 500:
                    abstract = abstract[:500] + "..."
            
            # Extract authors
            authors = []
            for author_elem in entry.findall(f"{self.ATOM_NS}author")[:5]:
                name_elem = author_elem.find(f"{self.ATOM_NS}name")
                if name_elem is not None and name_elem.text:
                    authors.append(Author(name=name_elem.text.strip()))
            
            if not authors:
                authors.append(Author(name="Unknown Author"))
            
            # Extract publication date
            published_elem = entry.find(f"{self.ATOM_NS}published")
            year = None
            if published_elem is not None and published_elem.text:
                try:
                    date = datetime.fromisoformat(published_elem.text.replace("Z", "+00:00"))
                    year = date.year
                except ValueError:
                    pass
            
            # Apply year filters
            if year:
                if year_min and year < year_min:
                    return None
                if year_max and year > year_max:
                    return None
            
            # Extract links
            pdf_url = None
            abstract_url = None
            for link in entry.findall(f"{self.ATOM_NS}link"):
                link_type = link.get("type", "")
                link_title = link.get("title", "")
                href = link.get("href", "")
                
                if link_title == "pdf" or link_type == "application/pdf":
                    pdf_url = href
                elif link.get("rel") == "alternate":
                    abstract_url = href
            
            # Construct PDF URL if not found directly
            if not pdf_url and arxiv_id:
                pdf_url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"
            
            # Extract DOI if available (via arXiv namespace)
            doi_elem = entry.find(f"{self.ARXIV_NS}doi")
            doi = doi_elem.text if doi_elem is not None else None
            
            # Primary URL - prefer abstract page
            url = abstract_url or f"https://arxiv.org/abs/{arxiv_id}"
            
            return SearchResult(
                id=f"arxiv:{arxiv_id}" if arxiv_id else "unknown",
                title=title,
                authors=authors,
                abstract=abstract,
                publication_year=year,
                source="arXiv",
                doi=doi,
                url=url,
                is_open_access=True,  # All arXiv preprints are open access
                open_access_url=pdf_url,
                cited_by_count=0,  # arXiv doesn't provide citation counts
                relevance_score=0.0
            )
            
        except Exception as e:
            print(f"Error parsing arXiv entry: {type(e).__name__}: {e}")
            return None
    
    def _extract_arxiv_id(self, url: str) -> str:
        """Extract arXiv ID from URL like http://arxiv.org/abs/2301.12345v1"""
        if not url:
            return ""
        
        # Match new format: 2301.12345 or 2301.12345v1
        match = re.search(r'(\d{4}\.\d{4,5})(v\d+)?', url)
        if match:
            return match.group(1)  # Return without version
        
        # Match old format: category/YYMMNNN
        match = re.search(r'([a-z-]+/\d{7})', url)
        if match:
            return match.group(1)
        
        return url.split("/")[-1] if "/" in url else url
