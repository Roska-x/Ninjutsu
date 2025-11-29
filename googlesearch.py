import requests
from dotenv import load_dotenv
import os
from typing import Dict, List, Optional, Any
from search_engine_interface import SearchEngineInterface, SearchEngineType

load_dotenv()

class GoogleSearch(SearchEngineInterface):
    """
    Google Custom Search implementation using Google Search API
    Implements the unified SearchEngineInterface
    """
    
    def __init__(self):
        self.api_key = os.getenv('API_KEY_GOOGLE')
        self.engine_id = os.getenv('SEARCH_ENGINE_ID')

    @property
    def engine_type(self) -> SearchEngineType:
        """Return the type of search engine"""
        return SearchEngineType.GOOGLE
    
    def build_url(self, query, num=10):
        return f'https://www.googleapis.com/customsearch/v1?key={self.api_key}&cx={self.engine_id}&q={query}&num={num}'
    
    def search(self, query: str, num: int = 10, **kwargs) -> Optional[Dict[str, Any]]:
        """
        Perform a basic search query
        Implements SearchEngineInterface requirement
        """
        url = self.build_url(query, num)
        try:
            response = requests.get(url)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"Error making request: {e}")
            return None
    
    def extract_results(self, data: Optional[Dict[str, Any]]) -> List[Dict[str, str]]:
        """
        Extract and standardize search results from Google API response
        Implements SearchEngineInterface requirement
        """
        if not data or 'items' not in data:
            return []
        
        results = []
        items = data.get('items', [])
        
        for result in items:
            # Extract standardized fields according to interface
            extracted = {
                'title': result.get('title', 'N/A'),
                'link': result.get('link', 'N/A'),
                'snippet': result.get('snippet', 'N/A'),
                'source': 'google'
            }
            
            # Add additional Google-specific metadata if available
            if 'displayLink' in result:
                extracted['display_link'] = result['displayLink']
            
            results.append(extracted)
        
        return results
    
    def display_results(self, results: List[Dict[str, str]], query: str = ""):
        """
        Display search results in a formatted manner
        Implements SearchEngineInterface requirement
        """
        if not results:
            print(f"No results found for query: {query}")
            return
        
        print(f"\n🔍 Google Results for: {query}")
        print(f"📊 Total results found: {len(results)}")
        print("=" * 80)
        
        for i, result in enumerate(results, 1):
            print(f"\n{i}. Title: {result.get('title', 'N/A')}")
            print(f"   Link: {result.get('link', 'N/A')}")
            print(f"   Snippet: {result.get('snippet', 'N/A')[:150]}...")
            print(f"   Source: {result.get('source', 'N/A')}")
            print("-" * 60)
    
    def search_books(self, query: str, num: int = 10, **kwargs) -> List[Dict[str, Any]]:
        """
        Search for books using Google Custom Search API
        Implements SearchEngineInterface requirement
        """
        # Enhance query with book-specific operators
        book_query = f"{query} filetype:pdf OR filetype:epub OR filetype:mobi"
        
        # Add book-specific keywords to help find relevant results
        if not any(keyword in query.lower() for keyword in ['book', 'ebook', 'pdf', 'textbook', 'manual']):
            book_query += " book OR ebook"
        
        url = self.build_url(book_query, num)
        
        try:
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()
            
            book_results = []
            if 'items' in data:
                for result in data['items']:
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
                            'source': 'google_books',
                            'book_score': score,  # Higher score = more book-like content
                            'display_link': result.get('displayLink', 'N/A')
                        })
            
            # Sort by book relevance score
            book_results.sort(key=lambda x: x.get('book_score', 0), reverse=True)
            
            return book_results
        except requests.RequestException as e:
            print(f"❌ Error searching books: {e}")
            return []

if __name__ == "__main__":
    # Simple CLI test for GoogleSearch using the unified interface
    searcher = GoogleSearch()
    query = input("Enter search query: ").strip()
    
    if not query:
        print("❌ Query cannot be empty")
    else:
        raw_results = searcher.search(query)
        standardized_results = searcher.extract_results(raw_results)
        searcher.display_results(standardized_results, query)