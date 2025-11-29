#!/usr/bin/env python3
"""
Selenium-based Google Search implementation.

Uses a real browser (Firefox via geckodriver) to perform Google searches
without requiring an API key, and exposes the unified SearchEngineInterface.

NOTE: This approach is heavier than the HTTP APIs and may be slower. It is
intended mainly as a fallback when no API keys are configured.
"""

from __future__ import annotations

import time
from typing import Any, Dict, List, Optional

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.firefox import GeckoDriverManager

from search_engine_interface import SearchEngineInterface, SearchEngineType


class SeleniumGoogleSearch(SearchEngineInterface):
    """
    Google search engine implementation backed by Selenium WebDriver.

    It opens https://www.google.com, performs a search, and scrapes the
    organic results from the first page. Results are standardized to match
    the rest of the toolkit.
    """

    def __init__(
        self,
        headless: bool = True,
        page_load_timeout: int = 20,
        wait_timeout: int = 10,
    ) -> None:
        """
        Initialize the Selenium Google search engine.

        Args:
            headless: Run the browser in headless mode (no GUI).
            page_load_timeout: Seconds to wait for page loads.
            wait_timeout: Seconds to wait for elements when scraping.
        """
        self.headless = headless
        self.page_load_timeout = page_load_timeout
        self.wait_timeout = wait_timeout

    @property
    def engine_type(self) -> SearchEngineType:
        """Return the type of search engine."""
        return SearchEngineType.SELENIUM_GOOGLE

    # ------------------------------------------------------------------
    # Core interface methods
    # ------------------------------------------------------------------
    def search(self, query: str, num: int = 10, **kwargs) -> Optional[Dict[str, Any]]:
        """
        Perform a basic search query using Selenium.

        This returns a raw structure that extract_results() will normalize:
            {"results": [ { "title": ..., "link": ..., "snippet": ... }, ... ]}
        """
        driver = self._create_driver()
        try:
            driver.get("https://www.google.com")
            self._accept_cookies(driver)
            self._perform_search(driver, query)

            # Give results some time to render
            time.sleep(2)

            raw_results = self._extract_results_from_page(driver, max_results=num)
            return {"results": raw_results}
        except Exception as exc:
            print(f"❌ Selenium Google search error: {exc}")
            return None
        finally:
            try:
                driver.quit()
            except Exception:
                pass

    def extract_results(self, data: Optional[Dict[str, Any]]) -> List[Dict[str, str]]:
        """
        Extract and standardize search results from the raw Selenium output.
        """
        if not data:
            return []

        items = data.get("results", [])
        results: List[Dict[str, str]] = []

        for item in items:
            results.append(
                {
                    "title": item.get("title", "N/A"),
                    "link": item.get("link", "N/A"),
                    "snippet": item.get("snippet", "N/A"),
                    "source": "selenium_google",
                }
            )

        return results

    def display_results(self, results: List[Dict[str, str]], query: str = "") -> None:
        """
        Display search results in a formatted manner.
        """
        if not results:
            print(f"❌ No Selenium Google results found for query: {query}")
            return

        print(f"\n🔍 Selenium (Google) results for: {query}")
        print(f"📊 Total results found: {len(results)}")
        print("=" * 80)

        for idx, result in enumerate(results, 1):
            print(f"\n{idx}. Title: {result.get('title', 'N/A')}")
            print(f"   Link: {result.get('link', 'N/A')}")
            snippet = result.get("snippet", "N/A")
            print(f"   Snippet: {snippet[:150]}...")
            print(f"   Source: {result.get('source', 'selenium_google')}")
            print("-" * 60)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _create_driver(self) -> webdriver.Firefox:
        """
        Create and configure a Firefox WebDriver instance.
        """
        options = webdriver.FirefoxOptions()
        if self.headless:
            options.add_argument("-headless")

        service = FirefoxService(GeckoDriverManager().install())
        driver = webdriver.Firefox(service=service, options=options)
        driver.set_page_load_timeout(self.page_load_timeout)
        return driver

    def _accept_cookies(self, driver: webdriver.Firefox) -> None:
        """
        Try to accept Google's cookie banner if it appears.
        """
        try:
            wait = WebDriverWait(driver, self.wait_timeout)
            # Common ID for the "I agree" button in many locales
            accept_button = wait.until(
                EC.element_to_be_clickable((By.ID, "L2AGLb"))
            )
            accept_button.click()
        except Exception:
            # Banner might not appear or may have a different structure; ignore.
            pass

    def _perform_search(self, driver: webdriver.Firefox, query: str) -> None:
        """
        Type the query into the search box and submit.
        """
        wait = WebDriverWait(driver, self.wait_timeout)
        search_box = wait.until(EC.presence_of_element_located((By.NAME, "q")))
        search_box.clear()
        search_box.send_keys(query)
        search_box.send_keys(Keys.ENTER)

    def _extract_results_from_page(
        self,
        driver: webdriver.Firefox,
        max_results: int = 10,
    ) -> List[Dict[str, str]]:
        """
        Scrape organic search results from the current results page.
        """
        results: List[Dict[str, str]] = []

        try:
            wait = WebDriverWait(driver, self.wait_timeout)
            wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.g")))
        except Exception:
            # If we can't wait for results, try to scrape whatever is there.
            pass

        cards = driver.find_elements(By.CSS_SELECTOR, "div.g")
        for card in cards:
            if len(results) >= max_results:
                break

            try:
                title_el = card.find_element(By.CSS_SELECTOR, "h3")
                link_el = card.find_element(By.TAG_NAME, "a")
                title = title_el.text.strip()
                link = link_el.get_attribute("href") or ""

                snippet = ""
                # Newer Google layout
                try:
                    snippet_el = card.find_element(By.CSS_SELECTOR, "div.VwiC3b")
                    snippet = snippet_el.text.strip()
                except Exception:
                    # Older / alternative layout
                    try:
                        snippet_el = card.find_element(By.CSS_SELECTOR, "span.aCOpRe")
                        snippet = snippet_el.text.strip()
                    except Exception:
                        snippet = ""

                if not title and not link:
                    continue

                results.append(
                    {
                        "title": title or link,
                        "link": link,
                        "snippet": snippet,
                    }
                )
            except Exception:
                # Skip cards that don't match the expected structure
                continue

        return results


if __name__ == "__main__":
    # Simple manual test
    engine = SeleniumGoogleSearch()
    q = input("Enter search query for Selenium Google: ").strip()
    if q:
        raw = engine.search(q, num=5)
        standardized = engine.extract_results(raw)
        engine.display_results(standardized, q)