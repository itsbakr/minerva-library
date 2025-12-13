import asyncio
from typing import List, Optional, Dict
from difflib import SequenceMatcher
from app.api.models import SearchResult, Author
from app.services.openalex import OpenAlexService
from app.services.crossref import CrossRefService
from app.services.unpaywall import UnpaywallService
import re

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
        # Note: Unpaywall doesn't have a public search API - it's only for DOI lookups
        # So we only search OpenAlex and CrossRef, then enrich with Unpaywall OA data
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
        
        db_names = ["OpenAlex", "CrossRef"]
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                print(f"Error in database {db_names[i]}: {result}")
                continue
            
            db_results, db_count = result
            all_results.extend(db_results)
            total_count += db_count
            
            if db_results:
                databases.append(db_names[i])
        
        # Enrich CrossRef/OpenAlex results with Unpaywall OA info
        # This is Unpaywall's primary purpose - checking DOIs for open access availability
        print(f"Enriching {len(all_results)} results with Unpaywall OA data...")
        results_before = sum(1 for r in all_results if r.is_open_access)
        all_results = await unpaywall.enrich_with_oa(all_results)
        results_after = sum(1 for r in all_results if r.is_open_access)
        
        # Add Unpaywall to databases list if it found any OA versions
        if results_after > results_before:
            databases.append("Unpaywall (OA enrichment)")
            print(f"Unpaywall found {results_after - results_before} additional open access versions")
        
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
        Deduplicate by MERGING duplicates (instead of dropping), using:
        1. Exact DOI match (most reliable)
        2. Exact normalized title match
        3. Fuzzy normalized title match (>92% similar)
        """
        if not results:
            return []

        # 1) Merge by DOI
        doi_groups: Dict[str, SearchResult] = {}
        no_doi: List[SearchResult] = []
        for r in results:
            doi_norm = self._normalize_doi(r.doi)
            if doi_norm:
                existing = doi_groups.get(doi_norm)
                doi_groups[doi_norm] = self._merge_results(existing, r) if existing else r
            else:
                no_doi.append(r)

        # 2) Merge by normalized title (exact first, then fuzzy) for no-DOI items
        title_groups: Dict[str, SearchResult] = {}
        title_keys: List[str] = []
        untitled: List[SearchResult] = []

        for r in no_doi:
            title_norm = self._normalize_title(r.title)
            if not title_norm:
                untitled.append(r)
                continue

            # Exact match
            if title_norm in title_groups:
                title_groups[title_norm] = self._merge_results(title_groups[title_norm], r)
                continue

            # Fuzzy match against already-seen titles
            best_key: Optional[str] = None
            best_sim = 0.0
            for key in title_keys:
                sim = self._calculate_similarity(title_norm, key)
                if sim > best_sim:
                    best_sim = sim
                    best_key = key

            if best_key and best_sim >= 0.92:
                title_groups[best_key] = self._merge_results(title_groups[best_key], r)
            else:
                title_groups[title_norm] = r
                title_keys.append(title_norm)

        # Keep untitled/no-DOI results as-is (can't confidently dedupe)
        merged = list(doi_groups.values()) + list(title_groups.values()) + untitled
        print(f"Deduplication (merge): {len(results)} → {len(merged)} results")
        return merged
    
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

    def _normalize_doi(self, doi: Optional[str]) -> Optional[str]:
        if not doi:
            return None
        d = doi.strip()
        if not d:
            return None
        d = d.replace("https://doi.org/", "").replace("http://dx.doi.org/", "")
        d = d.replace("http://doi.org/", "")
        d = d.strip().lower()
        return d or None

    def _normalize_title(self, title: Optional[str]) -> Optional[str]:
        if not title:
            return None
        t = title.strip().lower()
        if not t or t == "untitled":
            return None
        # collapse whitespace and remove most punctuation
        t = re.sub(r"\s+", " ", t)
        t = re.sub(r"[^\w\s]", "", t)
        t = t.strip()
        return t or None

    def _source_priority(self, source: str) -> int:
        # Smaller number = higher priority
        order = {
            "OpenAlex": 0,
            "CrossRef": 1,
            "Unpaywall": 2,
        }
        return order.get(source, 99)

    def _combine_sources(self, a: str, b: str) -> str:
        parts = set()
        for s in (a, b):
            if not s:
                continue
            for piece in s.split("+"):
                piece = piece.strip()
                if piece:
                    parts.add(piece)
        return "+".join(sorted(parts, key=self._source_priority)) if parts else (a or b)

    def _prefer_url(self, a: Optional[str], b: Optional[str]) -> Optional[str]:
        # Prefer PDF-ish links, otherwise keep first non-empty.
        if not a:
            return b
        if not b:
            return a
        a_pdf = (".pdf" in a.lower()) or ("pdf" in a.lower())
        b_pdf = (".pdf" in b.lower()) or ("pdf" in b.lower())
        if a_pdf and not b_pdf:
            return a
        if b_pdf and not a_pdf:
            return b
        # Prefer https://doi.org/ if one is DOI link and other is not
        a_doi = "doi.org" in a.lower()
        b_doi = "doi.org" in b.lower()
        if a_doi and not b_doi:
            return a
        if b_doi and not a_doi:
            return b
        return a

    def _merge_results(self, base: Optional[SearchResult], incoming: SearchResult) -> SearchResult:
        """
        Merge two results into one richer record.
        - Prefer OpenAlex as the primary metadata source when available
        - Union authors (by normalized name), keep up to 5
        - Keep the longest abstract
        - Keep max citation count
        - OR open access flags + prefer best OA URL
        """
        if base is None:
            return incoming

        # Decide which should be primary (for id/title defaults)
        if self._source_priority(incoming.source) < self._source_priority(base.source):
            primary, secondary = incoming, base
        else:
            primary, secondary = base, incoming

        # Authors union
        authors_by_name: Dict[str, str] = {}
        for r in (primary, secondary):
            for a in (r.authors or [])[:10]:
                key = re.sub(r"\s+", " ", (a.name or "").strip().lower())
                if key and key not in authors_by_name:
                    authors_by_name[key] = a.name.strip()
        merged_authors = [Author(name=name) for name in list(authors_by_name.values())[:5]]
        if not merged_authors:
            # fallback if authors list is empty on primary but present on secondary
            merged_authors = secondary.authors or []

        # Title: prefer non-empty, non-"Untitled", and longer title
        title_candidates = [primary.title, secondary.title]
        title_candidates = [t for t in title_candidates if t and t.strip() and t.strip().lower() != "untitled"]
        merged_title = max(title_candidates, key=lambda t: len(t.strip())) if title_candidates else (primary.title or secondary.title or "Untitled")

        # Abstract: prefer longer
        abs_a = primary.abstract or ""
        abs_b = secondary.abstract or ""
        merged_abstract = abs_a if len(abs_a) >= len(abs_b) else abs_b
        merged_abstract = merged_abstract or None

        # DOI normalize + prefer any existing DOI
        doi = self._normalize_doi(primary.doi) or self._normalize_doi(secondary.doi)

        # Publication year: prefer more recent non-null
        year = primary.publication_year or secondary.publication_year
        if primary.publication_year and secondary.publication_year:
            year = max(primary.publication_year, secondary.publication_year)

        # OA merge
        is_oa = bool(primary.is_open_access or secondary.is_open_access)
        oa_url = self._prefer_url(primary.open_access_url, secondary.open_access_url)

        # URL: prefer OA URL, otherwise prefer DOI URL, otherwise keep best existing
        url = self._prefer_url(primary.url, secondary.url)
        if oa_url:
            url = oa_url
        elif doi:
            url = url or f"https://doi.org/{doi}"

        # citations
        cited = max(primary.cited_by_count or 0, secondary.cited_by_count or 0)

        merged = SearchResult(
            id=primary.id if primary.id and primary.id != "unknown" else (secondary.id or "unknown"),
            title=merged_title,
            authors=merged_authors,
            abstract=merged_abstract,
            publication_year=year,
            source=self._combine_sources(primary.source, secondary.source),
            doi=doi,
            url=url,
            is_open_access=is_oa,
            open_access_url=oa_url,
            cited_by_count=cited,
            relevance_score=0.0,
        )
        return merged
    
    def _rank_results(self, results: List[SearchResult], query: str) -> List[SearchResult]:
        """Rank results by relevance (simple lexical + quality signals)"""
        q = (query or "").strip().lower()
        q_norm = re.sub(r"\s+", " ", re.sub(r"[^\w\s]", " ", q)).strip()
        stop = {
            "the", "a", "an", "of", "and", "or", "to", "in", "on", "for", "with", "by", "from", "at", "as",
        }
        q_words = [w for w in q_norm.split() if w and w not in stop]
        query_words = set(q_words)
        
        for result in results:
            score = 0.0
            title = (result.title or "").strip()
            title_norm = self._normalize_title(title) or ""
            abstract_norm = ""
            if result.abstract:
                abstract_norm = re.sub(r"\s+", " ", re.sub(r"[^\w\s]", " ", result.abstract.lower())).strip()
            
            # Open access bonus (increased weight)
            if result.is_open_access:
                score += 60  # Increased from 50
            if result.open_access_url:
                score += 10  # direct OA link quality boost
            
            # Recent publication bonus
            if result.publication_year:
                if result.publication_year >= 2023:
                    score += 30
                elif result.publication_year >= 2020:
                    score += 20
                elif result.publication_year >= 2015:
                    score += 10

            # DOI present = generally higher quality / easier to access
            if result.doi:
                score += 8
            
            # Citation count bonus (capped at 20 points)
            if result.cited_by_count:
                score += min(result.cited_by_count / 10, 20)
            
            # Title phrase + keyword matching
            if title_norm and query_words:
                title_words = set(title_norm.split())
                matches = len(query_words & title_words)
                score += matches * 12

                # Phrase boost if the normalized query appears in normalized title
                if q_norm and q_norm in title_norm:
                    score += 40

                # Coverage boost (how much of the query is present)
                coverage = matches / max(len(query_words), 1)
                score += coverage * 20

                # Soft similarity between query and title (helps short queries)
                score += self._calculate_similarity(q_norm, title_norm) * 15

            # Abstract keyword matching (lighter weight)
            if abstract_norm and query_words:
                abs_words = set(abstract_norm.split())
                abs_matches = len(query_words & abs_words)
                score += abs_matches * 4
                if q_norm and q_norm in abstract_norm:
                    score += 10

            # Penalize placeholder titles
            if (result.title or "").strip().lower() == "untitled":
                score -= 20
            
            result.relevance_score = round(score, 2)
        
        # Sort by score (descending)
        return sorted(results, key=lambda x: x.relevance_score, reverse=True)