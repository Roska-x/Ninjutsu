#!/usr/bin/env python3
"""
Dork catalog loader and helper utilities.

Provides a high-level API to access Google dork definitions stored in
`dorks_catalog.json`.
"""

import json
import os
from typing import List, Dict, Any, Optional, Set


class DorkCatalog:
    """Utility class to load and query dorks from a JSON catalog."""

    def __init__(self, catalog_path: str = "dorks_catalog.json") -> None:
        self.catalog_path = catalog_path
        self._dorks: List[Dict[str, Any]] = []
        self._loaded = False

    def _load_if_needed(self) -> None:
        if self._loaded:
            return

        if not os.path.exists(self.catalog_path):
            # Fail softly: keep empty catalog, caller can handle no dorks.
            self._dorks = []
            self._loaded = True
            return

        try:
            with open(self.catalog_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    self._dorks = data
                else:
                    # Allow {"dorks": [...]} format as well.
                    self._dorks = data.get("dorks", [])
        except (OSError, json.JSONDecodeError):
            self._dorks = []

        self._loaded = True

    @property
    def dorks(self) -> List[Dict[str, Any]]:
        """Return all dorks in the catalog."""
        self._load_if_needed()
        return list(self._dorks)

    def get_categories(self) -> List[str]:
        """Return a sorted list of category names present in the catalog."""
        self._load_if_needed()
        categories: Set[str] = set()
        for d in self._dorks:
            cat = d.get("category")
            if isinstance(cat, str) and cat:
                categories.add(cat)
        return sorted(categories)

    def get_by_category(self, category: str) -> List[Dict[str, Any]]:
        """Return all dorks that belong to a given category."""
        self._load_if_needed()
        return [d for d in self._dorks if d.get("category") == category]

    def get_by_id(self, dork_id: str) -> Optional[Dict[str, Any]]:
        """Return a single dork by its unique id."""
        self._load_if_needed()
        for d in self._dorks:
            if d.get("id") == dork_id:
                return d
        return None

    def search(self, term: str) -> List[Dict[str, Any]]:
        """Search dorks by simple substring match in title, query or tags."""
        self._load_if_needed()
        term = term.lower().strip()
        if not term:
            return []

        results: List[Dict[str, Any]] = []
        for d in self._dorks:
            title = str(d.get("title", "")).lower()
            query = str(d.get("query", "")).lower()
            tags = " ".join(map(str, d.get("tags", []))).lower()
            if term in title or term in query or term in tags:
                results.append(d)
        return results