#!/usr/bin/env python3
"""
Enhanced Dork Engine for executing dorks using multiple search engines.

It reads dork definitions from dorks_catalog.json via DorkCatalog and
supports both Google Custom Search and DuckDuckGo via SerAPI.
"""

import os
import time
from typing import Any, Dict, List, Optional

from search_engine_interface import SearchEngineType, create_search_manager, SearchResultComparator
from dork_catalog import DorkCatalog
from query_optimizer import QueryOptimizer, EngineAwareSearchManager


class DorkEngine:
    """Execute catalogued dorks using multiple search engines."""

    def __init__(self, engine_type: SearchEngineType = None, sleep_seconds: Optional[float] = None) -> None:
        """
        Initialize DorkEngine with support for multiple search engines
        
        Args:
            engine_type: Type of search engine to use (Google or DuckDuckGo)
                        If None, will auto-select based on availability
            sleep_seconds: Rate limiting delay between requests
        """
        # Initialize search manager
        self.search_manager = create_search_manager()
        
        # Optional: wrap with EngineAwareSearchManager for per-engine query optimization
        try:
            self.engine_aware_manager = EngineAwareSearchManager(self.search_manager)
        except Exception:
            self.engine_aware_manager = None
        
        # Set search engine
        if engine_type:
            try:
                self.search_manager.set_engine(engine_type)
                self.current_engine_type = engine_type
            except ValueError:
                # Fallback to auto-selection
                self._auto_select_engine()
        else:
            self._auto_select_engine()
        
        self.catalog = DorkCatalog()
        
        # Set sleep time for rate limiting
        env_sleep = os.getenv("GOOGLE_SLEEP_SECONDS")
        if sleep_seconds is not None:
            self.sleep_seconds = float(sleep_seconds)
        elif env_sleep:
            try:
                self.sleep_seconds = float(env_sleep)
            except ValueError:
                self.sleep_seconds = 1.0
        else:
            self.sleep_seconds = 1.0
        
        print(f"🔍 DorkEngine initialized with {self.current_engine_type.value if self.current_engine_type else 'auto-select'} engine")
        
        # Initialize query optimizer
        try:
            self.query_optimizer = QueryOptimizer()
            print("✅ Query optimizer enabled")
        except ImportError:
            self.query_optimizer = None
            print("⚠️  Query optimizer not available")
    
    def _auto_select_engine(self):
        """Automatically select the best available search engine"""
        available_engines = self.search_manager.get_available_engines()

        if not available_engines:
            print("❌ No search engines available!")
            self.current_engine_type = None
            return

        # Priority: Serper (Google) > Google > DuckDuckGo > Selenium > Any available
        priority_engines = [
            SearchEngineType.SERPER_GOOGLE,
            SearchEngineType.GOOGLE,
            SearchEngineType.DUCKDUCKGO,
            SearchEngineType.SELENIUM_GOOGLE,
        ]

        for engine_type in priority_engines:
            if engine_type in available_engines:
                self.search_manager.set_engine(engine_type)
                self.current_engine_type = engine_type
                return

        # Fallback to first available engine
        self.search_manager.set_engine(available_engines[0])
        self.current_engine_type = available_engines[0]
    
    def auto_select_engine(self):
        """
        Public helper to auto-select the best available search engine.
        Intended for use by higher-level orchestrators (e.g. MasterSecurityTool)
        when enabling global auto-select mode.
        """
        self._auto_select_engine()
        if self.current_engine_type:
            print(f"✅ Auto-selected engine for DorkEngine: {self.current_engine_type.value}")
        else:
            print("⚠️  DorkEngine could not auto-select any engine")
    
    def set_engine(self, engine_type: SearchEngineType):
        """Set the search engine to use"""
        try:
            self.search_manager.set_engine(engine_type)
            self.current_engine_type = engine_type
            print(f"✅ Engine changed to {engine_type.value}")
        except ValueError as e:
            print(f"❌ Could not set {engine_type.value} engine: {e}")
    
    def get_current_engine(self) -> SearchEngineType:
        """Get the current search engine type"""
        return self.current_engine_type
    
    def get_engine_info(self) -> Dict[str, Any]:
        """Get information about the current engine and available engines"""
        return {
            'current_engine': self.current_engine_type.value if self.current_engine_type else None,
            'available_engines': [e.value for e in self.search_manager.get_available_engines()],
            'sleep_seconds': self.sleep_seconds,
            'query_optimizer_available': self.query_optimizer is not None
        }
    
    def _optimize_query(self, query: str, verbose: bool = False) -> str:
        """
        Optimize query using query optimizer if available
        
        Args:
            query: Original search query
            verbose: Whether to show optimization details
        
        Returns:
            Optimized query
        """
        if not self.query_optimizer or not self.current_engine_type:
            return query
        
        optimized_query = self.query_optimizer.optimize_query(query, self.current_engine_type)
        
        if optimized_query != query and verbose:
            print(f"🔧 Optimized query: {optimized_query}")
        
        return optimized_query
    
    def _analyze_query_compatibility(self, query: str) -> dict:
        """
        Analyze query compatibility with current engine
        
        Args:
            query: Query to analyze
        
        Returns:
            Compatibility analysis
        """
        if not self.query_optimizer:
            return {'recommendation': 'Query optimizer not available'}
        
        return self.query_optimizer.analyze_query_compatibility(query)

    def _sleep(self) -> None:
        """Respect rate limiting between Google API calls."""
        if self.sleep_seconds > 0:
            time.sleep(self.sleep_seconds)

    @staticmethod
    def deduplicate_results(results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate results based on the 'link' field."""
        seen = set()
        deduped: List[Dict[str, Any]] = []
        for item in results:
            link = item.get("link")
            if not link or link in seen:
                continue
            seen.add(link)
            deduped.append(item)
        return deduped

    def _format_query(self, template: str, placeholders: Optional[Dict[str, str]] = None) -> str:
        """Safely format a dork query template with placeholders."""
        if not placeholders:
            return template
        safe_placeholders: Dict[str, str] = {k: (v or "") for k, v in placeholders.items()}
        try:
            return template.format(**safe_placeholders)
        except Exception:
            # If formatting fails, fall back to raw template to avoid crashing.
            return template

    def run_dork(
        self,
        dork: Dict[str, Any],
        placeholders: Optional[Dict[str, str]] = None,
        num: int = 10,
        verbose: bool = False,
    ) -> List[Dict[str, Any]]:
        """Execute a single dork definition and return raw search results (items)."""
        query_template = str(dork.get("query", ""))
        query = self._format_query(query_template, placeholders)
        if verbose:
            print(f"  Query: {query}")
        
        # Analyze query compatibility
        compatibility = self._analyze_query_compatibility(query)
        if verbose and compatibility.get('recommendation') != 'Query optimizer not available':
            print(f"  💡 {compatibility.get('recommendation', 'No recommendation')}")
        
        # Optimize query for current engine
        optimized_query = self._optimize_query(query, verbose)
        
        try:
            # Use the unified search manager
            results = self.search_manager.search(optimized_query, num=num)
            self._sleep()  # rate limiting
            return results or []
        except Exception as e:
            print(f"❌ Error running dork: {e}")
            return []
    
    def run_dork_cross_engine(
        self,
        dork: Dict[str, Any],
        placeholders: Optional[Dict[str, str]] = None,
        num: int = 10,
        verbose: bool = False,
    ) -> Dict[str, Any]:
        """
        Execute a single dork definition across multiple engines
        
        Returns:
            Dictionary with results from each engine
        """
        query_template = str(dork.get("query", ""))
        query = self._format_query(query_template, placeholders)
        if verbose:
            print(f"  Cross-engine query: {query}")
        
        try:
            # If we have an engine-aware manager, use per-engine optimized queries
            if getattr(self, "engine_aware_manager", None):
                results_by_engine = self.engine_aware_manager.cross_engine_search_with_optimization(query, num)
                
                # Build comparison structure similar to UnifiedSearchManager.compare_results
                all_urls = set()
                engine_urls = {}
                
                for engine_type, engine_results in results_by_engine.items():
                    urls = {result.get('link', '') for result in engine_results if result.get('link')}
                    engine_urls[engine_type] = urls
                    all_urls.update(urls)
                
                overlaps = {}
                for engine_type in engine_urls:
                    overlaps[engine_type] = (
                        len(all_urls.intersection(engine_urls[engine_type])) / len(all_urls)
                        if all_urls else 0
                    )
                
                comparison = {
                    "query": query,
                    "total_unique_urls": len(all_urls),
                    "results_by_engine": results_by_engine,
                    "overlap_percentage": overlaps,
                    "engines_tested": list(results_by_engine.keys())
                }
            else:
                # Fallback to manager's built-in comparison
                comparison = self.search_manager.compare_results(query, num)
            
            self._sleep()  # rate limiting
            return comparison
        except Exception as e:
            print(f"❌ Error running cross-engine dork: {e}")
            return {}

    def run_dork_by_id(
        self,
        dork_id: str,
        placeholders: Optional[Dict[str, str]] = None,
        num: int = 10,
        verbose: bool = False,
    ) -> List[Dict[str, Any]]:
        """Convenience wrapper to execute a dork by its id from the catalog."""
        dork = self.catalog.get_by_id(dork_id)
        if not dork:
            if verbose:
                print(f"❌ Dork with id '{dork_id}' not found in catalog")
            return []
        return self.run_dork(dork, placeholders=placeholders, num=num, verbose=verbose)
    
    def run_dork_by_id_cross_engine(
        self,
        dork_id: str,
        placeholders: Optional[Dict[str, str]] = None,
        num: int = 10,
        verbose: bool = False,
    ) -> Dict[str, Any]:
        """Execute a dork by ID across multiple engines."""
        dork = self.catalog.get_by_id(dork_id)
        if not dork:
            if verbose:
                print(f"❌ Dork with id '{dork_id}' not found in catalog")
            return {}
        return self.run_dork_cross_engine(dork, placeholders=placeholders, num=num, verbose=verbose)

    def run_category(
        self,
        category: str,
        placeholders: Optional[Dict[str, str]] = None,
        num_per_dork: int = 10,
        verbose: bool = False,
    ) -> Dict[str, Any]:
        """
        Execute all dorks for a given category.

        Returns a dict with:
            {
              "combined": [ ... all unique results ... ],
              "by_dork": { dork_id: [results], ... }
            }
        """
        dorks = self.catalog.get_by_category(category)
        all_results: List[Dict[str, Any]] = []
        by_dork: Dict[str, List[Dict[str, Any]]] = {}
        if verbose:
            print(f"\n🔍 Running {len(dorks)} dorks for category: {category} using {self.current_engine_type.value}")
        
        for d in dorks:
            dork_id = d.get("id", "unknown")
            if verbose:
                title = d.get("title", dork_id)
                print(f"\n▶ {title} ({dork_id})")
            items = self.run_dork(d, placeholders=placeholders, num=num_per_dork, verbose=verbose)
            by_dork[dork_id] = items
            all_results.extend(items)
        combined = self.deduplicate_results(all_results)
        return {"combined": combined, "by_dork": by_dork}
    
    def run_category_cross_engine(
        self,
        category: str,
        placeholders: Optional[Dict[str, str]] = None,
        num_per_dork: int = 10,
        verbose: bool = False,
    ) -> Dict[str, Any]:
        """
        Execute all dorks for a given category across multiple engines.

        Returns a comprehensive dict with results from all engines and cross-engine analysis,
        including a deduplicated, ranked combined result list.
        """
        dorks = self.catalog.get_by_category(category)
        if verbose:
            print(f"\n🔍 Cross-engine execution for category: {category}")
            print(f"Engines: {[e.value for e in self.search_manager.get_available_engines()]}")

        cross_engine_results: Dict[str, Any] = {}

        for d in dorks:
            dork_id = d.get("id", "unknown")
            if verbose:
                title = d.get("title", dork_id)
                print(f"\n▶ {title} ({dork_id})")

            # Run cross-engine for this dork
            cross_result = self.run_dork_cross_engine(
                d,
                placeholders=placeholders,
                num=num_per_dork,
                verbose=verbose,
            )
            cross_engine_results[dork_id] = cross_result

        # Combine results across all dorks and engines
        all_results_by_engine: Dict[SearchEngineType, List[Dict[str, Any]]] = {}
        total_unique_urls: set[str] = set()

        for dork_id, dork_result in cross_engine_results.items():
            results_by_engine = dork_result.get("results_by_engine", {})

            for engine_type, results in results_by_engine.items():
                if engine_type not in all_results_by_engine:
                    all_results_by_engine[engine_type] = []
                all_results_by_engine[engine_type].extend(results)

                # Collect unique URLs
                for result in results:
                    url = result.get("link")
                    if url:
                        total_unique_urls.add(url)

        # Calculate overlap percentages
        overlap_percentages: Dict[SearchEngineType, float] = {}
        engines = list(all_results_by_engine.keys())

        for engine in engines:
            engine_urls = {r.get("link") for r in all_results_by_engine[engine] if r.get("link")}
            overlap = (
                len(total_unique_urls.intersection(engine_urls)) / len(total_unique_urls)
                if total_unique_urls
                else 0
            )
            overlap_percentages[engine] = overlap

        # Build a best_combined list using SearchResultComparator
        results_list: List[List[Dict[str, Any]]] = list(all_results_by_engine.values())
        if results_list:
            # Limit the number of combined results to something reasonable
            top_n = min(len(total_unique_urls), num_per_dork * max(1, len(dorks)))
            best_combined = SearchResultComparator.get_best_results(results_list, top_n=top_n)
            total_quality_score = SearchResultComparator.calculate_quality_score(best_combined)
        else:
            best_combined = []
            total_quality_score = 0.0

        return {
            "cross_engine_results": cross_engine_results,
            "combined_by_engine": all_results_by_engine,
            "total_unique_urls": len(total_unique_urls),
            "overlap_percentage": overlap_percentages,
            "engines_tested": engines,
            "category": category,
            "total_dorks": len(dorks),
            "best_combined": best_combined,
            "total_quality_score": total_quality_score,
        }
    
    def compare_dork_performance(self, dork_id: str, placeholders: Optional[Dict[str, str]] = None, num: int = 10) -> Dict[str, Any]:
        """
        Compare performance of a specific dork across different engines
        
        Args:
            dork_id: ID of the dork to compare
            placeholders: Query placeholders
            num: Number of results per engine
        
        Returns:
            Performance comparison data
        """
        return self.run_dork_by_id_cross_engine(dork_id, placeholders, num, verbose=True)

    def search_pdf_books(
        self,
        title: str,
        author: Optional[str] = None,
        topic: Optional[str] = None,
        lang: Optional[str] = None,
        num_per_dork: int = 5,
        verbose: bool = False,
    ) -> Dict[str, Any]:
        """
        High-level helper to search for PDF books using the pdf_books category.

        The catalog defines several templates that use placeholders:
        - {title} (required)
        - {author} (optional)
        - {topic} (optional)
        - language-specific hints are encoded directly in the queries.
        """
        if not title.strip():
            raise ValueError("Title cannot be empty for PDF search")
        placeholders = {
            "title": title.strip(),
            "author": (author or "").strip(),
            "topic": (topic or "").strip(),
        }
        
        # For now, lang is only used to choose which templates to prioritise;
        # we still execute all pdf_books templates because they are cheap.
        dorks = self.catalog.get_by_category("pdf_books")
        if lang:
            lang = lang.lower()
            if lang in ("es", "spanish"):
                # Move spanish-hint dorks to the front.
                dorks = sorted(
                    dorks,
                    key=lambda d: "spanish" not in " ".join(d.get("tags", [])).lower(),
                )
            elif lang in ("en", "eng", "english"):
                dorks = sorted(
                    dorks,
                    key=lambda d: "english" not in " ".join(d.get("tags", [])).lower(),
                )
        
        all_results: List[Dict[str, Any]] = []
        by_dork: Dict[str, List[Dict[str, Any]]] = {}
        
        if verbose:
            print(f"\n📚 Searching PDF books for: {title} using {self.current_engine_type.value}")
        
        for d in dorks:
            dork_id = d.get("id", "unknown")
            if verbose:
                print(f"\n▶ Using template: {d.get('title', dork_id)}")
            items = self.run_dork(d, placeholders=placeholders, num=num_per_dork, verbose=verbose)
            by_dork[dork_id] = items
            all_results.extend(items)
        
        combined = self.deduplicate_results(all_results)
        return {"combined": combined, "by_dork": by_dork}
    
    def search_pdf_books_cross_engine(
        self,
        title: str,
        author: Optional[str] = None,
        topic: Optional[str] = None,
        lang: Optional[str] = None,
        num_per_dork: int = 5,
        verbose: bool = False,
    ) -> Dict[str, Any]:
        """
        Search for PDF books across multiple engines
        """
        if not title.strip():
            raise ValueError("Title cannot be empty for PDF search")
        
        placeholders = {
            "title": title.strip(),
            "author": (author or "").strip(),
            "topic": (topic or "").strip(),
        }
        
        dorks = self.catalog.get_by_category("pdf_books")
        
        if verbose:
            print(f"\n📚 Cross-engine PDF search for: {title}")
            print(f"Engines: {[e.value for e in self.search_manager.get_available_engines()]}")
        
        cross_engine_results = {}
        
        for d in dorks:
            dork_id = d.get("id", "unknown")
            if verbose:
                print(f"\n▶ Using template: {d.get('title', dork_id)}")
            
            cross_result = self.run_dork_cross_engine(d, placeholders=placeholders, num=num_per_dork, verbose=verbose)
            cross_engine_results[dork_id] = cross_result
        
        return {
            "cross_engine_results": cross_engine_results,
            "search_params": {
                "title": title,
                "author": author,
                "topic": topic,
                "lang": lang,
                "num_per_dork": num_per_dork
            }
        }