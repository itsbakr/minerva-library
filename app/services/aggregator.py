import asyncio
from typing import List
from app.api.models import SearchResult
from app.services.openalex import OpenAlexService
from app.services.crossref import CrossRefService

class SearchAggregator:
    async def search_all(
        self,
        query: str,
        page: int = 1,
        per_page: int = 20,
        year_min=None,
        year_max=None,
        open_access_only=False
    ) -> tuple[List[SearchResult], int, List[str]]:
        """
        Search all databases in parallel
        Returns: (combined_results, total_count, databases_searched)
        """
        
        # Create service instances
        openalex = OpenAlexService()
        crossref = CrossRefService()
        
        # Create search tasks for parallel execution
        # Note: CrossRef doesn't support open_access_only filter
        tasks = [
            openalex.search(
                query=query, 
                page=page, 
                per_page=per_page,
                year_min=year_min,
                year_max=year_max,
                open_access_only=open_access_only
            ),
            crossref.search(
                query=query,
                page=page,
                per_page=per_page,
                year_min=year_min,
                year_max=year_max
            )
        ]
        
        # Execute all searches simultaneously
        try:
            results = await asyncio.gather(*tasks, return_exceptions=True)
        except Exception as e:
            print(f"Error in gather: {e}")
            return [], 0, []
        
        # Combine results
        all_results = []
        total_count = 0
        databases = []
        
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                print(f"Error in database {i}: {result}")
                continue
            
            db_results, db_count = result
            
            # If open_access_only is True, filter CrossRef results
            if i == 1 and open_access_only:  # CrossRef results
                # We'll filter these after checking with Unpaywall later
                # For now, just include them
                pass
            
            all_results.extend(db_results)
            total_count += db_count
            
            db_name = "OpenAlex" if i == 0 else "CrossRef"
            if db_results:
                databases.append(db_name)
        
        # Remove duplicates
        deduplicated = self._deduplicate(all_results)
        
        # Filter for open access if requested
        if open_access_only:
            deduplicated = [r for r in deduplicated if r.is_open_access]
        
        # Rank by relevance
        ranked = self._rank_results(deduplicated, query)
        
        # Return all results (pagination handled by frontend or later)
        return ranked, len(ranked), databases
    
    def _deduplicate(self, results: List[SearchResult]) -> List[SearchResult]:
        """Remove duplicate results based on DOI and title"""
        seen_dois = set()
        seen_titles = set()
        unique_results = []
        
        for result in results:
            # Check DOI first (most reliable)
            if result.doi and result.doi.strip():
                doi_normalized = result.doi.strip().lower()
                if doi_normalized in seen_dois:
                    continue
                seen_dois.add(doi_normalized)
            
            # Check title (normalized)
            if result.title:
                title_normalized = result.title.lower().strip()
                if title_normalized in seen_titles:
                    continue
                seen_titles.add(title_normalized)
            
            unique_results.append(result)
        
        return unique_results
    
    def _rank_results(self, results: List[SearchResult], query: str) -> List[SearchResult]:
        """Rank results by relevance"""
        query_words = set(query.lower().split())
        
        for result in results:
            score = 0.0
            
            # Open access bonus
            if result.is_open_access:
                score += 50
            
            # Recent publication bonus
            if result.publication_year:
                if result.publication_year >= 2023:
                    score += 30
                elif result.publication_year >= 2020:
                    score += 20
                elif result.publication_year >= 2015:
                    score += 10
            
            # Citation count bonus (capped at 20 points)
            if result.cited_by_count:
                score += min(result.cited_by_count / 10, 20)
            
            # Title keyword matching
            if result.title:
                title_words = set(result.title.lower().split())
                matches = len(query_words & title_words)
                score += matches * 10
            
            result.relevance_score = round(score, 2)
        
        # Sort by score (descending)
        return sorted(results, key=lambda x: x.relevance_score, reverse=True)