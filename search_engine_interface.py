#!/usr/bin/env python3
"""
Search Engine Interface
Abstract base class for unified search functionality across multiple engines
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from enum import Enum

class SearchEngineType(Enum):
    """Supported search engine types"""
    GOOGLE = "google"
    DUCKDUCKGO = "duckduckgo"
    SERPER_GOOGLE = "serper_google"
    SELENIUM_GOOGLE = "selenium_google"

class SearchEngineInterface(ABC):
    """
    Abstract base class for search engines
    Defines the common interface that all search engines must implement
    """
    
    @property
    @abstractmethod
    def engine_type(self) -> SearchEngineType:
        """Return the type of search engine"""
        pass
    
    @abstractmethod
    def search(self, query: str, num: int = 10, **kwargs) -> Optional[Dict[str, Any]]:
        """
        Perform a basic search query
        
        Args:
            query: Search query string
            num: Number of results to return (default: 10)
            **kwargs: Additional search parameters
        
        Returns:
            Raw search results from the engine
        """
        pass
    
    @abstractmethod
    def extract_results(self, data: Optional[Dict[str, Any]]) -> List[Dict[str, str]]:
        """
        Extract and standardize search results
        
        Args:
            data: Raw search results from the engine
        
        Returns:
            List of standardized result dictionaries with keys:
            - title: Result title
            - link: Result URL
            - snippet: Result snippet/description
            - source: Search engine identifier
        """
        pass
    
    @abstractmethod
    def display_results(self, results: List[Dict[str, str]], query: str = ""):
        """
        Display search results in a formatted manner
        
        Args:
            results: List of standardized results
            query: Original search query for display
        """
        pass
    
    def advanced_search(self, query: str, num: int = 10, **kwargs) -> List[Dict[str, str]]:
        """
        Perform advanced search with additional parameters
        
        Args:
            query: Search query string
            num: Number of results to return
            **kwargs: Additional search parameters (region, safe_search, etc.)
        
        Returns:
            List of standardized results
        """
        data = self.search(query, num, **kwargs)
        return self.extract_results(data)
    
    def search_with_fallback(self, query: str, num: int = 10, **kwargs) -> List[Dict[str, str]]:
        """
        Search with fallback mechanism - retry on failure
        
        Args:
            query: Search query string
            num: Number of results to return
            **kwargs: Additional search parameters
        
        Returns:
            List of standardized results
        """
        try:
            return self.advanced_search(query, num, **kwargs)
        except Exception as e:
            print(f"⚠️  Search failed for {self.engine_type.value}: {e}")
            print(f"🔄 Retrying with fallback parameters...")
            
            # Retry with minimal parameters
            try:
                return self.advanced_search(query, min(num, 5))
            except Exception as fallback_error:
                print(f"❌ Fallback search also failed: {fallback_error}")
                return []
    
    # Advanced result type methods
    def search_images(self, query: str, num: int = 10, **kwargs) -> List[Dict[str, Any]]:
        """
        Search for images
        
        Args:
            query: Search query string
            num: Number of results to return
            **kwargs: Additional search parameters
        
        Returns:
            List of image results with metadata
        """
        # Default implementation - should be overridden by engines that support it
        print(f"⚠️  {self.engine_type.value} does not support image search")
        return []
    
    def search_news(self, query: str, num: int = 10, **kwargs) -> List[Dict[str, Any]]:
        """
        Search for news
        
        Args:
            query: Search query string
            num: Number of results to return
            **kwargs: Additional search parameters
        
        Returns:
            List of news results with metadata
        """
        # Default implementation - should be overridden by engines that support it
        print(f"⚠️  {self.engine_type.value} does not support news search")
        return []
    
    def search_books(self, query: str, num: int = 10, **kwargs) -> List[Dict[str, Any]]:
        """
        Search for books
        
        Args:
            query: Search query string
            num: Number of results to return
            **kwargs: Additional search parameters
        
        Returns:
            List of book results with metadata
        """
        # Default implementation - should be overridden by engines that support it
        print(f"⚠️  {self.engine_type.value} does not support book search")
        return []
    
    def get_trending_searches(self, region: str = "us-en") -> List[str]:
        """
        Get trending searches for a region
        
        Args:
            region: Region code (e.g., 'us-en', 'es-es')
        
        Returns:
            List of trending search queries
        """
        # Default implementation - should be overridden by engines that support it
        print(f"⚠️  {self.engine_type.value} does not support trending searches")
        return []

class UnifiedSearchManager:
    """
    Manager class for handling multiple search engines
    Provides unified interface for switching between engines and comparing results
    """
    
    def __init__(self):
        self.engines: Dict[SearchEngineType, SearchEngineInterface] = {}
        self.current_engine: Optional[SearchEngineType] = None
    
    def register_engine(self, engine_type: SearchEngineType, engine: SearchEngineInterface):
        """
        Register a search engine implementation
        
        Args:
            engine_type: Type of the search engine
            engine: Implementation of the search engine
        """
        self.engines[engine_type] = engine
        
        # Set as current engine if none exists
        if self.current_engine is None:
            self.current_engine = engine_type
    
    def set_engine(self, engine_type: SearchEngineType):
        """
        Set the current search engine
        
        Args:
            engine_type: Type of search engine to use
        """
        if engine_type not in self.engines:
            raise ValueError(f"Engine {engine_type.value} not registered")
        
        self.current_engine = engine_type
    
    def get_engine(self, engine_type: Optional[SearchEngineType] = None) -> SearchEngineInterface:
        """
        Get a search engine instance
        
        Args:
            engine_type: Specific engine type, or None for current engine
        
        Returns:
            Search engine implementation
        """
        if engine_type is None:
            engine_type = self.current_engine
        
        if engine_type is None or engine_type not in self.engines:
            raise ValueError("No search engine selected")
        
        return self.engines[engine_type]
    
    def search(self, query: str, num: int = 10, **kwargs) -> List[Dict[str, str]]:
        """
        Search using the current engine, with built-in fallback
        
        Args:
            query: Search query string
            num: Number of results to return
            **kwargs: Additional search parameters
        
        Returns:
            List of standardized results
        """
        engine = self.get_engine()
        # Use the engine's fallback-aware search to improve robustness
        return engine.search_with_fallback(query, num, **kwargs)
    
    def search_multiple_engines(self, query: str, num: int = 10, 
                               engines: Optional[List[SearchEngineType]] = None) -> Dict[SearchEngineType, List[Dict[str, str]]]:
        """
        Search across multiple engines and compare results
        
        Args:
            query: Search query string
            num: Number of results per engine
            engines: List of engines to search (None for all)
        
        Returns:
            Dictionary mapping engine types to their results
        """
        if engines is None:
            engines = list(self.engines.keys())
        
        results = {}
        
        for engine_type in engines:
            if engine_type in self.engines:
                try:
                    print(f"🔍 Searching with {engine_type.value}...")
                    engine = self.engines[engine_type]
                    # Use fallback-aware search for each engine
                    results[engine_type] = engine.search_with_fallback(query, num)
                except Exception as e:
                    print(f"❌ Error searching with {engine_type.value}: {e}")
                    results[engine_type] = []
        
        return results
    
    def compare_results(self, query: str, num: int = 10) -> Dict[str, Any]:
        """
        Compare results across multiple search engines
        
        Args:
            query: Search query string
            num: Number of results per engine
        
        Returns:
            Dictionary with comparison data
        """
        results = self.search_multiple_engines(query, num)
        
        # Find unique URLs across all engines
        all_urls = set()
        engine_urls = {}
        
        for engine_type, engine_results in results.items():
            urls = {result.get('link', '') for result in engine_results if result.get('link')}
            engine_urls[engine_type] = urls
            all_urls.update(urls)
        
        # Calculate overlaps
        overlaps = {}
        for engine_type in engine_urls:
            overlaps[engine_type] = len(all_urls.intersection(engine_urls[engine_type])) / len(all_urls) if all_urls else 0
        
        return {
            'query': query,
            'total_unique_urls': len(all_urls),
            'results_by_engine': results,
            'overlap_percentage': overlaps,
            'engines_tested': list(results.keys())
        }
    
    def search_images(self, query: str, num: int = 10, **kwargs) -> List[Dict[str, Any]]:
        """
        Search for images using the current engine.

        Engines that do not support image search will fall back to the
        default implementation in SearchEngineInterface and return [].
        """
        engine = self.get_engine()
        return engine.search_images(query, num, **kwargs)
    
    def search_news(self, query: str, num: int = 10, **kwargs) -> List[Dict[str, Any]]:
        """
        Search for news using the current engine.

        Engines that do not support news search will fall back to the
        default implementation in SearchEngineInterface and return [].
        """
        engine = self.get_engine()
        return engine.search_news(query, num, **kwargs)
    
    def search_books(self, query: str, num: int = 10, **kwargs) -> List[Dict[str, Any]]:
        """
        Search for books using the current engine.

        Engines that do not support book search will fall back to the
        default implementation in SearchEngineInterface and return [].
        """
        engine = self.get_engine()
        return engine.search_books(query, num, **kwargs)
    
    def get_trending_searches(self, region: str = "us-en") -> List[str]:
        """
        Get trending searches using the current engine.

        Engines that do not support trending searches will fall back to the
        default implementation in SearchEngineInterface and return [].
        """
        engine = self.get_engine()
        return engine.get_trending_searches(region)
    
    def get_available_engines(self) -> List[SearchEngineType]:
        """Get list of available search engines"""
        return list(self.engines.keys())
    
    def get_current_engine(self) -> Optional[SearchEngineType]:
        """Get the currently selected search engine"""
        return self.current_engine
    
    def display_engine_status(self):
        """Display status of all registered engines"""
        print("🔍 Search Engine Status")
        print("=" * 50)
        
        for engine_type, engine in self.engines.items():
            status = "✅ Active" if engine_type == self.current_engine else "ℹ️  Available"
            print(f"{status} {engine_type.value.title()}")
        
        if self.current_engine:
            print(f"\nCurrent Engine: {self.current_engine.value.title()}")
        else:
            print("\n❌ No engine selected")

class SearchResultComparator:
    """
    Utility class for comparing and analyzing search results across engines
    """
    
    @staticmethod
    def find_duplicates(results_list: List[List[Dict[str, str]]]) -> Dict[str, List[int]]:
        """
        Find duplicate results across multiple result sets
        
        Args:
            results_list: List of result lists from different engines
        
        Returns:
            Dictionary mapping URLs to list of engine indices that found them
        """
        url_engines = {}
        
        for engine_idx, results in enumerate(results_list):
            for result in results:
                url = result.get('link', '')
                if url:
                    if url not in url_engines:
                        url_engines[url] = []
                    url_engines[url].append(engine_idx)
        
        # Only return duplicates (found by multiple engines)
        return {url: engines for url, engines in url_engines.items() if len(engines) > 1}
    
    @staticmethod
    def calculate_quality_score(results: List[Dict[str, str]]) -> float:
        """
        Calculate a quality score for search results based on various factors
        
        Args:
            results: List of search results
        
        Returns:
            Quality score between 0 and 1
        """
        if not results:
            return 0.0
        
        score = 0.0
        total_factors = 4
        
        # Factor 1: Results with snippets
        results_with_snippets = sum(1 for r in results if r.get('snippet', '').strip())
        score += results_with_snippets / len(results)
        
        # Factor 2: Results with meaningful titles
        meaningful_titles = sum(1 for r in results if len(r.get('title', '').strip()) > 10)
        score += meaningful_titles / len(results)
        
        # Factor 3: HTTPS results (security factor)
        https_results = sum(1 for r in results if r.get('link', '').startswith('https://'))
        score += https_results / len(results)
        
        # Factor 4: Results from reputable domains
        reputable_domains = ['github.com', 'stackoverflow.com', 'docs.', 'wikipedia.org']
        reputable_count = sum(1 for r in results 
                            if any(domain in r.get('link', '') for domain in reputable_domains))
        score += reputable_count / len(results)
        
        return score / total_factors
    
    @staticmethod
    def get_best_results(results_list: List[List[Dict[str, str]]], top_n: int = 10) -> List[Dict[str, str]]:
        """
        Get the best results from multiple engine result sets
        
        Args:
            results_list: List of result lists from different engines
            top_n: Number of top results to return
        
        Returns:
            List of the best results with their scores
        """
        all_results = []
        
        # Combine all results
        for engine_idx, results in enumerate(results_list):
            for result in results:
                result_copy = result.copy()
                result_copy['engine_index'] = engine_idx
                all_results.append(result_copy)
        
        # Score and sort results
        scored_results = []
        for result in all_results:
            score = SearchResultComparator.calculate_quality_score([result])
            result_copy = result.copy()
            result_copy['quality_score'] = score
            scored_results.append(result_copy)
        
        # Sort by quality score and return top results
        scored_results.sort(key=lambda x: x['quality_score'], reverse=True)
        return scored_results[:top_n]

# Factory function for creating search managers
def create_search_manager() -> UnifiedSearchManager:
    """
    Factory function to create a configured search manager
    
    Returns:
        UnifiedSearchManager instance with basic configuration
    """
    manager = UnifiedSearchManager()
    
    # Try to import and register available engines
    try:
        from googlesearch import GoogleSearch
        from duckduckgo_serpapi import DuckDuckGoSerpAPI
        from serper_google import SerperGoogleSearch
        
        # Register Serper-based Google Search (if configured)
        try:
            serper_engine = SerperGoogleSearch()
            manager.register_engine(SearchEngineType.SERPER_GOOGLE, serper_engine)
            print("✅ Serper (Google) engine registered successfully")
        except Exception as e:
            print(f"⚠️  Serper engine not available: {e}")
        
        # Register Google Custom Search (if configured)
        try:
            google_engine = GoogleSearch()
            manager.register_engine(SearchEngineType.GOOGLE, google_engine)
            print("✅ Google Custom Search engine registered successfully")
        except Exception as e:
            print(f"⚠️  Google Custom Search engine not available: {e}")
        
        # Register DuckDuckGo Search (via SerpAPI)
        try:
            duckduckgo_engine = DuckDuckGoSerpAPI()
            manager.register_engine(SearchEngineType.DUCKDUCKGO, duckduckgo_engine)
            print("✅ DuckDuckGo (SerpAPI) engine registered successfully")
        except Exception as e:
            print(f"⚠️  DuckDuckGo SerpAPI engine not available: {e}")
        
        # Register Selenium-based Google Search (no API key required)
        try:
            from selenium_google import SeleniumGoogleSearch
            selenium_engine = SeleniumGoogleSearch()
            manager.register_engine(SearchEngineType.SELENIUM_GOOGLE, selenium_engine)
            print("✅ Selenium (Google WebDriver) engine registered successfully")
        except ImportError as e:
            print(f"⚠️  Selenium Google engine module not available: {e}")
        except Exception as e:
            print(f"⚠️  Selenium Google engine not available: {e}")
        
    except ImportError as e:
        print(f"⚠️  Some engines could not be imported: {e}")
        print("Make sure all required dependencies are installed")
    
    return manager

if __name__ == "__main__":
    # Test the search engine interface
    print("🔍 Testing Search Engine Interface")
    print("=" * 50)
    
    try:
        # Create search manager
        manager = create_search_manager()
        manager.display_engine_status()
        
        # Test search with current engine
        query = input("\nEnter search query: ")
        if query:
            results = manager.search(query, num=5)
            
            if results:
                print(f"\n📊 Found {len(results)} results")
                for i, result in enumerate(results, 1):
                    print(f"{i}. {result.get('title', 'N/A')}")
                    print(f"   URL: {result.get('link', 'N/A')}")
            else:
                print("❌ No results found")
                
    except Exception as e:
        print(f"❌ Error: {e}")
        print("Check your .env file configuration")