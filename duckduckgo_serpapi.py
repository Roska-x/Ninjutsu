#!/usr/bin/env python3
"""
DuckDuckGo Search API using SerAPI service
Advanced search capabilities with DuckDuckGo for security research
"""

import requests
from dotenv import load_dotenv
import os
import time
from typing import Dict, List, Optional, Any
from urllib.parse import quote
from search_engine_interface import SearchEngineInterface, SearchEngineType

load_dotenv()

class DuckDuckGoSerpAPI(SearchEngineInterface):
    """
    DuckDuckGo search implementation using SerAPI service
    Provides advanced search capabilities for security research and credential discovery
    Implements the unified SearchEngineInterface
    """
    
    @property
    def engine_type(self) -> SearchEngineType:
        """Return the type of search engine"""
        return SearchEngineType.DUCKDUCKGO
    
    def __init__(self):
        self.api_key = os.getenv('SERP_API_KEY')
        self.base_url = "https://serpapi.com/search"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        if not self.api_key:
            raise ValueError("SERP_API_KEY not found in environment variables")
    
    def build_url(self, query: str, num: int = 10, **kwargs) -> str:
        """
        Build SerpAPI URL for DuckDuckGo search following official parameters.
        
        Docs: https://serpapi.com/duckduckgo-search-api
        - q      : query string
        - kl     : region (e.g. us-en, es-es)
        - safe   : 1 (Strict), -1 (Moderate, default), -2 (Off)
        - df     : date filter (d, w, m, y or custom range)
        - m      : max number of results (1–50)
        """
        params = {
            "engine": "duckduckgo",
            "q": query,
            "api_key": self.api_key,
            "output": "json",
        }
        
        # Results per page -> `m` (not `num` for DuckDuckGo)
        try:
            m = int(num)
        except (TypeError, ValueError):
            m = 10
        m = max(1, min(m, 50))
        params["m"] = m
        
        # Localization: prefer explicit `kl`, then `region`, default us-en
        kl = kwargs.pop("kl", None) or kwargs.pop("region", None) or "us-en"
        params["kl"] = kl
        
        # Safe search: map friendly strings to numeric values expected by SerpAPI
        # Docs: 1 = Strict, -1 = Moderate (default), -2 = Off
        safe_search = kwargs.pop("safe_search", None) or kwargs.pop("safe", None)
        safe_value = None
        if isinstance(safe_search, str):
            mapping = {
                "strict": 1,
                "active": 1,     # backwards compatible with previous code
                "moderate": -1,
                "default": -1,
                "off": -2,
                "none": -2,
            }
            safe_value = mapping.get(safe_search.lower())
        elif isinstance(safe_search, (int, float)):
            safe_value = int(safe_search)
        
        if safe_value is None:
            safe_value = -1  # SerpAPI default for DuckDuckGo
        
        params["safe"] = safe_value
        
        # Date filter: map high-level time_range to DuckDuckGo `df`
        time_range = kwargs.pop("time_range", None)
        if time_range:
            tr = str(time_range).lower()
            df_map = {
                "day": "d",
                "d": "d",
                "week": "w",
                "w": "w",
                "month": "m",
                "m": "m",
                "year": "y",
                "y": "y",
            }
            params["df"] = df_map.get(tr, time_range)
        
        # Pass through any remaining SerpAPI-specific parameters
        # (e.g., start, no_cache, async, json_restrictor, etc.)
        for key, value in kwargs.items():
            if value is not None:
                params[key] = value
        
        # Build query string
        query_string = "&".join([f"{k}={quote(str(v))}" for k, v in params.items()])
        return f"{self.base_url}?{query_string}"
    
    def search(self, query: str, num: int = 10, **kwargs) -> Optional[Dict[str, Any]]:
        """
        Perform DuckDuckGo search via SerAPI
        """
        url = self.build_url(query, num, **kwargs)
        
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"❌ Error making SerAPI request: {e}")
            return None
    
    def extract_results(self, data: Optional[Dict[str, Any]]) -> List[Dict[str, str]]:
        """
        Extract and standardize search results from SerAPI response
        Implements the SearchEngineInterface requirement
        """
        if not data or 'organic_results' not in data:
            return []
        
        results = []
        organic_results = data.get('organic_results', [])
        
        for result in organic_results:
            # Extract standardized fields according to interface
            extracted = {
                'title': result.get('title', 'N/A'),
                'link': result.get('link', 'N/A'),
                'snippet': result.get('snippet', result.get('description', 'N/A')),
                'source': 'duckduckgo'
            }
            
            # Add additional metadata if available
            if 'rich_snippet' in result:
                extracted['rich_snippet'] = result['rich_snippet']
            
            if 'thumbnail' in result:
                extracted['thumbnail'] = result['thumbnail']
            
            results.append(extracted)
        
        return results
    
    def display_results(self, results: List[Dict[str, str]], query: str = ""):
        """
        Display search results in a formatted manner
        """
        if not results:
            print(f"❌ No results found for query: {query}")
            return
        
        print(f"\n🔍 DuckDuckGo Results for: {query}")
        print(f"📊 Total results found: {len(results)}")
        print("=" * 80)
        
        for i, result in enumerate(results, 1):
            print(f"\n{i}. Title: {result.get('title', 'N/A')}")
            print(f"   Link: {result.get('link', 'N/A')}")
            print(f"   Snippet: {result.get('snippet', 'N/A')[:150]}...")
            print(f"   Source: {result.get('source', 'N/A')}")
            print("-" * 60)
    
    def advanced_search(self, query: str, num: int = 10, region: str = "us-en",
                       safe_search: str = "active", **kwargs) -> List[Dict[str, str]]:
        """
        Perform advanced search with additional parameters.
        
        Wrapper around search() that exposes higher-level arguments and lets
        build_url() translate them into the correct SerpAPI parameters.
        """
        additional_params = {
            "kl": region,                         # maps to DuckDuckGo localization
            "safe_search": safe_search,           # mapped to numeric `safe` in build_url()
            "time_range": kwargs.get("time_range"),       # mapped to `df`
            "exclude_domains": kwargs.get("exclude_domains"),
            "include_domains": kwargs.get("include_domains"),
        }
        
        data = self.search(query, num, **additional_params)
        return self.extract_results(data)
    
    def search_with_operators(self, query: str, operators: List[str], num: int = 10) -> List[Dict[str, str]]:
        """
        Search using DuckDuckGo-specific operators
        """
        # Combine query with operators
        enhanced_query = f"{query} {' '.join(operators)}"
        
        print(f"🔍 Enhanced query: {enhanced_query}")
        return self.advanced_search(enhanced_query, num, safe_search='active')
    
    def get_related_queries(self, query: str) -> List[str]:
        """
        Get related search queries (suggestions)
        """
        params = {
            'engine': 'duckduckgo_suggestions',
            'q': query,
            'api_key': self.api_key
        }
        
        url = f"{self.base_url}?{ '&'.join([f'{k}={quote(str(v))}' for k, v in params.items()]) }"
        
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            suggestions = []
            if 'suggestions' in data:
                for suggestion in data['suggestions']:
                    suggestions.append(suggestion.get('value', ''))
            
            return suggestions
        except requests.RequestException as e:
            print(f"❌ Error getting suggestions: {e}")
            return []
    
    def get_trending_searches(self, region: str = "us-en") -> List[str]:
        """
        Get trending searches for a specific region
        Implements SearchEngineInterface requirement
        """
        params = {
            'engine': 'duckduckgo_trending_searches',
            'region': region,
            'api_key': self.api_key
        }
        
        url = f"{self.base_url}?{ '&'.join([f'{k}={quote(str(v))}' for k, v in params.items()]) }"
        
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            trending = []
            if 'trending_searches' in data:
                for trend in data['trending_searches']:
                    trending.append(trend.get('query', ''))
            
            return trending
        except requests.RequestException as e:
            print(f"❌ Error getting trending searches: {e}")
            return []
    
    def search_images(self, query: str, num: int = 10, **kwargs) -> List[Dict[str, Any]]:
        """
        Search for images using DuckDuckGo
        Implements SearchEngineInterface requirement
        """
        params = {
            'engine': 'duckduckgo_images',
            'q': query,
            'api_key': self.api_key,
            'num': num
        }
        
        url = f"{self.base_url}?{ '&'.join([f'{k}={quote(str(v))}' for k, v in params.items()]) }"
        
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            image_results = []
            if 'images_results' in data:
                for image in data['images_results']:
                    image_results.append({
                        'title': image.get('title', 'N/A'),
                        'link': image.get('link', 'N/A'),
                        'thumbnail': image.get('thumbnail', 'N/A'),
                        'original': image.get('original', 'N/A'),
                        'source': 'duckduckgo_images'
                    })
            
            return image_results
        except requests.RequestException as e:
            print(f"❌ Error searching images: {e}")
            return []
    
    def search_news(self, query: str, num: int = 10, **kwargs) -> List[Dict[str, Any]]:
        """
        Search for news using DuckDuckGo
        Implements SearchEngineInterface requirement
        """
        params = {
            'engine': 'duckduckgo_news',
            'q': query,
            'api_key': self.api_key,
            'num': num
        }
        
        time_range = kwargs.get('time_range')
        if time_range:
            params['time_range'] = time_range
        
        url = f"{self.base_url}?{ '&'.join([f'{k}={quote(str(v))}' for k, v in params.items()]) }"
        
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            news_results = []
            if 'news_results' in data:
                for news in data['news_results']:
                    news_results.append({
                        'title': news.get('title', 'N/A'),
                        'link': news.get('link', 'N/A'),
                        'snippet': news.get('snippet', 'N/A'),
                        'date': news.get('date', 'N/A'),
                        'source': news.get('source', 'N/A')
                    })
            
            return news_results
        except requests.RequestException as e:
            print(f"❌ Error searching news: {e}")
            return []
    
    def search_books(self, query: str, num: int = 10, **kwargs) -> List[Dict[str, Any]]:
        """
        Search for books using DuckDuckGo
        Implements SearchEngineInterface requirement
        """
        # Enhance query with book-specific operators for better results
        book_query = f"{query} filetype:pdf OR filetype:epub OR filetype:mobi"
        
        # Add book-specific keywords to help find relevant results
        if not any(keyword in query.lower() for keyword in ['book', 'ebook', 'pdf', 'textbook', 'manual']):
            book_query += " book OR ebook"
        
        params = {
            'engine': 'duckduckgo',
            'q': book_query,
            'api_key': self.api_key,
            'm': num
        }
        
        # Use safe search for book content
        params['safe'] = 1  # Strict safe search
        
        # Add region preference if specified
        region = kwargs.get('region', 'us-en')
        params['kl'] = region
        
        # Build URL
        query_string = "&".join([f"{k}={quote(str(v))}" for k, v in params.items()])
        url = f"{self.base_url}?{query_string}"
        
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            book_results = []
            if 'organic_results' in data:
                for result in data['organic_results']:
                    # Filter results that are more likely to be books
                    title = result.get('title', '').lower()
                    snippet = result.get('snippet', '').lower()
                    
                    # Score based on book-related keywords
                    book_indicators = ['book', 'ebook', 'pdf', 'chapter', 'author', 'publisher', 'isbn', 'textbook', 'manual']
                    score = sum(1 for indicator in book_indicators if indicator in title or indicator in snippet)
                    
                    # Only include results with some book-related keywords
                    if score > 0:
                        book_results.append({
                            'title': result.get('title', 'N/A'),
                            'link': result.get('link', 'N/A'),
                            'snippet': result.get('snippet', 'N/A'),
                            'source': 'duckduckgo_books',
                            'book_score': score,  # Higher score = more book-like content
                            'date': result.get('date', 'N/A'),
                            'thumbnail': result.get('thumbnail', 'N/A')
                        })
            
            # Sort by book relevance score
            book_results.sort(key=lambda x: x.get('book_score', 0), reverse=True)
            
            return book_results
        except requests.RequestException as e:
            print(f"❌ Error searching books: {e}")
            return []

# Security-focused search methods
class SecurityDuckDuckGoSearch(DuckDuckGoSerpAPI):
    """
    Extended DuckDuckGo search class with security-focused methods
    """
    
    def find_sensitive_files(self, filetype: str, domain: str = None) -> List[Dict[str, str]]:
        """
        Search for sensitive files using DuckDuckGo
        """
        query_parts = [f"filetype:{filetype}"]
        
        if domain:
            query_parts.append(f"site:{domain}")
        
        query_parts.extend([
            "password OR secret OR key OR credential",
            "intitle:index.of OR inurl:admin OR inurl:config"
        ])
        
        query = " ".join(query_parts)
        return self.advanced_search(query, num=15)
    
    def search_exposed_configs(self, config_type: str, domain: str = None) -> List[Dict[str, str]]:
        """
        Search for exposed configuration files
        """
        config_keywords = {
            'env': ['.env', 'environment', 'config'],
            'database': ['database.yml', 'db_config', 'connection_string'],
            'api': ['api_key', 'secret_key', 'oauth', 'jwt'],
            'cloud': ['aws_access_key', 'azure', 'gcp', 'terraform']
        }
        
        if config_type not in config_keywords:
            config_type = 'env'
        
        keywords = " OR ".join(config_keywords[config_type])
        query_parts = [f"({keywords})"]
        
        if domain:
            query_parts.append(f"site:{domain}")
        
        query_parts.extend([
            "inurl:config OR inurl:settings OR inurl:conf",
            "intitle:index.of OR filetype:txt OR filetype:yml"
        ])
        
        query = " ".join(query_parts)
        return self.advanced_search(query, num=15)
    
    def check_domain_security(self, domain: str) -> Dict[str, List[Dict[str, str]]]:
        """
        Perform comprehensive security check for a domain
        """
        results = {}
        
        # Check for common sensitive files
        print(f"🔍 Checking domain: {domain}")
        
        # Environment files
        print("  Checking for .env files...")
        results['env_files'] = self.find_sensitive_files('env', domain)
        time.sleep(1)
        
        # Configuration files
        print("  Checking for config files...")
        results['config_files'] = self.search_exposed_configs('config', domain)
        time.sleep(1)
        
        # API documentation
        print("  Checking for API docs...")
        query = f"site:{domain} (api OR swagger OR graphql) (documentation OR docs)"
        results['api_docs'] = self.advanced_search(query, num=10)
        time.sleep(1)
        
        # Admin panels
        print("  Checking for admin panels...")
        admin_query = f"site:{domain} (admin OR wp-admin OR login OR dashboard)"
        results['admin_panels'] = self.advanced_search(admin_query, num=10)
        time.sleep(1)
        
        return results

if __name__ == "__main__":
    # Test the DuckDuckGo search implementation
    try:
        searcher = SecurityDuckDuckGoSearch()
        query = input("Enter search query: ")
        
        print("\n🔍 DuckDuckGo Search Test")
        print("=" * 50)
        
        results = searcher.search(query)
        if results:
            standardized_results = searcher.extract_results(results)
            searcher.display_results(standardized_results, query)
        else:
            print("❌ No results found or error occurred")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        print("Make sure you have SERP_API_KEY in your .env file")