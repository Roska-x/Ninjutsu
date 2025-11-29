#!/usr/bin/env python3
"""
Demonstration of DuckDuckGo Book Search Functionality
Shows how to search for books using the new book search feature
"""

import os
import sys
from dotenv import load_dotenv

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

load_dotenv()

from search_engine_interface import create_search_manager, SearchEngineType

def demo_duckduckgo_book_search():
    """Demonstrate DuckDuckGo book search functionality"""
    print("📚 DuckDuckGo Book Search Demonstration")
    print("=" * 50)
    
    # Create search manager
    manager = create_search_manager()
    
    # Set to DuckDuckGo engine for book search
    try:
        manager.set_engine(SearchEngineType.DUCKDUCKGO)
        print("✅ Using DuckDuckGo for book search")
    except:
        print("❌ DuckDuckGo engine not available")
        return
    
    # Example book searches
    book_queries = [
        {
            "query": "artificial intelligence textbook",
            "description": "AI textbook search"
        },
        {
            "query": "python programming book pdf",
            "description": "Python programming book search"
        },
        {
            "query": "machine learning handbook",
            "description": "Machine learning handbook search"
        }
    ]
    
    for search in book_queries:
        query = search["query"]
        description = search["description"]
        
        print(f"\n🔍 {description}: '{query}'")
        print("-" * 40)
        
        try:
            # Perform book search
            results = manager.search_books(query, num=3)
            
            if results:
                print(f"✅ Found {len(results)} book results:")
                
                for i, result in enumerate(results, 1):
                    print(f"\n{i}. 📖 {result.get('title', 'N/A')}")
                    print(f"   📄 {result.get('snippet', 'N/A')[:80]}...")
                    print(f"   🔗 {result.get('link', 'N/A')}")
                    print(f"   📊 Relevance score: {result.get('book_score', 'N/A')}")
                    
            else:
                print("❌ No book results found")
                
        except Exception as e:
            print(f"❌ Error: {e}")
    
    print(f"\n🎉 Book search demo completed!")
    print("\n💡 Book search features:")
    print("   • Automatically enhances queries with filetype filters (PDF, EPUB, MOBI)")
    print("   • Filters results for book-related content")
    print("   • Provides relevance scoring for better results")
    print("   • Works with both individual engines and unified interface")

def demo_direct_engine_usage():
    """Show direct usage of the DuckDuckGo engine"""
    print("\n🔧 Direct DuckDuckGo Engine Usage")
    print("=" * 40)
    
    try:
        from duckduckgo_serpapi import SecurityDuckDuckGoSearch
        
        # Create DuckDuckGo engine directly
        engine = SecurityDuckDuckGoSearch()
        print("✅ DuckDuckGo engine initialized")
        
        query = "cybersecurity fundamentals book"
        
        # Perform book search
        print(f"\n🔍 Searching for: '{query}'")
        results = engine.search_books(query, num=3)
        
        if results:
            print(f"✅ Found {len(results)} book results:")
            for i, result in enumerate(results, 1):
                print(f"\n{i}. {result.get('title', 'N/A')}")
                print(f"   🔗 {result.get('link', 'N/A')}")
                print(f"   📊 Score: {result.get('book_score', 'N/A')}")
        
    except Exception as e:
        print(f"❌ Error with direct engine usage: {e}")

if __name__ == "__main__":
    try:
        demo_duckduckgo_book_search()
        demo_direct_engine_usage()
        
        print("\n" + "="*60)
        print("🎯 SUCCESS: DuckDuckGo book search is now available!")
        print("📖 You can now search for books using:")
        print("   • manager.search_books(query, num=10)")
        print("   • engine.search_books(query, num=10, region='es-es')")
        print("   • Enhanced with book-specific filtering and scoring")
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")