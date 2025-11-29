#!/usr/bin/env python3
"""
Serper-based Google Search implementation
Integrates google.serper.dev with the unified search interface.
"""

import os
from typing import Dict, List, Optional, Any

import requests
from dotenv import load_dotenv

from search_engine_interface import SearchEngineInterface, SearchEngineType

load_dotenv()


class SerperGoogleSearch(SearchEngineInterface):
    """
    Google Search implementation backed by Serper (google.serper.dev).
    """

    @property
    def engine_type(self) -> SearchEngineType:
        """Return the type of search engine."""
        return SearchEngineType.SERPER_GOOGLE

    def __init__(self):
        self.api_key = os.getenv("SERPER_API_KEY")
        self.base_url = os.getenv("SERPER_BASE_URL", "https://google.serper.dev/search")

        if not self.api_key:
            raise ValueError("SERPER_API_KEY not found in environment variables")

        self.session = requests.Session()
        self.session.headers.update(
            {
                "X-API-KEY": self.api_key,
                "Content-Type": "application/json",
            }
        )

    def search(self, query: str, num: int = 10, **kwargs) -> Optional[Dict[str, Any]]:
        """
        Perform a Serper search request.

        Docs: https://serper.dev
        """
        payload: Dict[str, Any] = {
            "q": query,
            "num": num,
        }

        # Optional localization / type parameters passed via kwargs
        gl = kwargs.get("gl") or kwargs.get("region")
        if gl:
            payload["gl"] = gl

        hl = kwargs.get("hl") or kwargs.get("lang")
        if hl:
            payload["hl"] = hl

        search_type = kwargs.get("type")
        if search_type:
            payload["type"] = search_type

        try:
            response = self.session.post(self.base_url, json=payload, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as exc:
            print(f"❌ Error making Serper request: {exc}")
            return None

    def extract_results(self, data: Optional[Dict[str, Any]]) -> List[Dict[str, str]]:
        """
        Extract and standardize search results from Serper response.
        """
        if not data:
            return []

        organic = data.get("organic", []) or data.get("results", [])
        results: List[Dict[str, str]] = []

        for item in organic:
            result = {
                "title": item.get("title", "N/A"),
                "link": item.get("link", "N/A"),
                "snippet": item.get("snippet", item.get("snippet_highlighted", "N/A")),
                "source": "serper_google",
            }
            results.append(result)

        return results

    def display_results(self, results: List[Dict[str, str]], query: str = "") -> None:
        """
        Display search results in a formatted manner.
        """
        if not results:
            print(f"❌ No results found for query: {query}")
            return

        print(f"\n🔍 Serper (Google) results for: {query}")
        print(f"📊 Total results found: {len(results)}")
        print("=" * 80)

        for idx, result in enumerate(results, 1):
            print(f"\n{idx}. Title: {result.get('title', 'N/A')}")
            print(f"   Link: {result.get('link', 'N/A')}")
            print(f"   Snippet: {result.get('snippet', 'N/A')[:150]}...")
            print(f"   Source: {result.get('source', 'N/A')}")
            print("-" * 60)


if __name__ == "__main__":
    try:
        searcher = SerperGoogleSearch()
        query = input("Enter search query: ").strip()

        if not query:
            print("❌ Query cannot be empty")
        else:
            raw_results = searcher.search(query)
            standardized_results = searcher.extract_results(raw_results)
            searcher.display_results(standardized_results, query)
    except Exception as exc:
        print(f"❌ Error: {exc}")
        print("Make sure SERPER_API_KEY is set in your environment or .env file")