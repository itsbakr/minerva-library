import asyncio
from typing import List
from difflib import SequenceMatcher
from app.api.models import SearchResult
from app.services.openalex import OpenAlexService
from app.services.crossref import CrossRefService
from app.services.unpaywall import UnpaywallService

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
        Search all databases in parallel and enrich with Unpaywall
        Returns: (combined_results, total_count, databases_searched)
        """
        
        # Create service instances
        openalex = OpenAlexService()
        crossref = CrossRefService()
        unpaywall = UnpaywallService()
        
        # Create search tasks for parallel execution
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
            ),
            unpaywall.search(
                query=query,
                page=page,
                per_page=per_page // 2  # Unpaywall typically returns fewer results
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
            all_results.extend(db_results)
            total_count += db_count
            
            db_names = ["OpenAlex", "CrossRef", "Unpaywall"]
            if db_results:
                databases.append(db_names[i])
        
        # Enrich CrossRef/OpenAlex results with Unpaywall OA info
        print(f"Enriching {len(all_results)} results with Unpaywall OA data...")
        all_results = await unpaywall.enrich_with_oa(all_results)
        
        # Remove duplicates
        deduplicated = self._deduplicate(all_results)
        
        # Filter for open access if requested
        if open_access_only:
            deduplicated = [r for r in deduplicated if r.is_open_access]
        
        # Rank by relevance
        ranked = self._rank_results(deduplicated, query)
        
        return ranked, len(ranked), databases
    
    def _deduplicate(self, results: List[SearchResult]) -> List[SearchResult]:
        """
        Remove duplicate results using multiple strategies:
        1. Exact DOI match
        2. Exact title match
        3. Fuzzy title match (>90% similar)
        """
        seen_dois = set()
        seen_titles = {}  # title -> result mapping for fuzzy comparison
        unique_results = []
        
        for result in results:
            is_duplicate = False
            
            # Strategy 1: Check DOI (most reliable)
            if result.doi and result.doi.strip():
                doi_normalized = result.doi.strip().lower()
                if doi_normalized in seen_dois:
                    is_duplicate = True
                else:
                    seen_dois.add(doi_normalized)
            
            # Strategy 2: Check exact title match
            if not is_duplicate and result.title:
                title_normalized = result.title.lower().strip()
                
                # Check exact match
                if title_normalized in seen_titles:
                    is_duplicate = True
                else:
                    # Strategy 3: Check fuzzy match against all seen titles
                    for seen_title, seen_result in seen_titles.items():
                        similarity = self._calculate_similarity(
                            title_normalized, 
                            seen_title
                        )
                        
                        if similarity > 0.90:  # 90% similar = duplicate
                            is_duplicate = True
                            # Keep the one with more metadata
                            if self._has_more_metadata(result, seen_result):
                                # Replace old one with new one
                                unique_results.remove(seen_result)
                                unique_results.append(result)
                                seen_titles[title_normalized] = result
                            break
                    
                    if not is_duplicate:
                        seen_titles[title_normalized] = result
            
            if not is_duplicate:
                unique_results.append(result)
        
        print(f"Deduplication: {len(results)} → {len(unique_results)} results")
        return unique_results
    
    def _calculate_similarity(self, str1: str, str2: str) -> float:
        """Calculate similarity ratio between two strings (0-1)"""
        return SequenceMatcher(None, str1, str2).ratio()
    
    def _has_more_metadata(self, result1: SearchResult, result2: SearchResult) -> bool:
        """Compare two results and return True if result1 has more metadata"""
        score1 = sum([
            bool(result1.abstract),
            bool(result1.doi),
            bool(result1.open_access_url),
            len(result1.authors),
            bool(result1.publication_year)
        ])
        
        score2 = sum([
            bool(result2.abstract),
            bool(result2.doi),
            bool(result2.open_access_url),
            len(result2.authors),
            bool(result2.publication_year)
        ])
        
        return score1 > score2
    
    def _rank_results(self, results: List[SearchResult], query: str) -> List[SearchResult]:
        """Rank results by relevance"""
        query_words = set(query.lower().split())
        
        for result in results:
            score = 0.0
            
            # Open access bonus (increased weight)
            if result.is_open_access:
                score += 60  # Increased from 50
            
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