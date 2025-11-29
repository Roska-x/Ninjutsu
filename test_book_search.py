#!/usr/bin/env python3
"""
Test script for book search functionality
Demonstrates book search using both Google and DuckDuckGo engines
"""

import os
import sys
from dotenv import load_dotenv

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

load_dotenv()

from search_engine_interface import create_search_manager, SearchEngineType

def test_book_search():
    """Test book search functionality across different engines"""
    print("📚 Testing Book Search Functionality")
    print("=" * 60)
    
    # Create search manager
    manager = create_search_manager()
    
    # Display available engines
    print("🔍 Available Search Engines:")
    manager.display_engine_status()
    print()
    
    # Test query for books
    test_queries = [
        "machine learning algorithms",
        "python programming tutorial",
        "data science handbook"
    ]
    
    for query in test_queries:
        print(f"\n🔍 Searching for books: '{query}'")
        print("-" * 50)
        
        # Test with available engines
        for engine_type in manager.get_available_engines():
            try:
                print(f"\n📖 Using {engine_type.value.title()}:")
                engine = manager.get_engine(engine_type)
                
                # Perform book search
                results = engine.search_books(query, num=5)
                
                if results:
                    print(f"✅ Found {len(results)} book-related results:")
                    for i, result in enumerate(results[:3], 1):  # Show first 3 results
                        print(f"  {i}. {result.get('title', 'N/A')}")
                        print(f"     📄 {result.get('snippet', 'N/A')[:100]}...")
                        print(f"     🔗 {result.get('link', 'N/A')}")
                        if 'book_score' in result:
                            print(f"     📊 Book relevance score: {result['book_score']}")
                        print()
                else:
                    print("❌ No book results found")
                    
            except Exception as e:
                print(f"❌ Error with {engine_type.value}: {e}")
        
        print("=" * 60)

def test_unified_book_search():
    """Test unified book search interface"""
    print("\n🔄 Testing Unified Book Search Interface")
    print("=" * 60)
    
    manager = create_search_manager()
    
    if not manager.get_available_engines():
        print("❌ No search engines available")
        return
    
    # Set engine to first available
    engine_type = manager.get_available_engines()[0]
    manager.set_engine(engine_type)
    
    query = "cybersecurity fundamentals"
    print(f"🔍 Unified book search for: '{query}'")
    
    try:
        # Use the unified interface
        results = manager.search_books(query, num=3)
        
        if results:
            print(f"✅ Found {len(results)} results using unified interface:")
            for i, result in enumerate(results, 1):
                print(f"\n{i}. {result.get('title', 'N/A')}")
                print(f"   Link: {result.get('link', 'N/A')}")
                print(f"   Source: {result.get('source', 'N/A')}")
        else:
            print("❌ No results found")
            
    except Exception as e:
        print(f"❌ Error with unified search: {e}")

if __name__ == "__main__":
    try:
        test_book_search()
        test_unified_book_search()
        
        print("\n🎉 Book search functionality test completed!")
        print("\n📖 Usage Examples:")
        print("  - SearchManager.search_books(query, num=10)")
        print("  - Engine.search_books(query, num=10, region='es-es')")
        print("  - Enhanced with filetype filters and book-specific keywords")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        print("\n💡 Make sure your .env file is configured with:")
        print("   - API_KEY_GOOGLE and SEARCH_ENGINE_ID for Google")
        print("   - SERP_API_KEY for DuckDuckGo")