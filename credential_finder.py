#!/usr/bin/env python3
"""
Advanced Credential Finder Tool
Finds credentials, .env files, .config files, API endpoints using Google Dorking and DuckDuckGo search
Enhanced with support for multiple search engines
"""

import requests
from dotenv import load_dotenv
import os
import json
import time
from urllib.parse import urljoin, urlparse
import re
from typing import List, Dict, Optional, Any
from search_engine_interface import (
    UnifiedSearchManager,
    SearchEngineType,
    create_search_manager,
    SearchResultComparator
)
from query_optimizer import QueryOptimizer, EngineAwareSearchManager

load_dotenv()

# Diccionario completo de patrones regex para detectar API keys y secretos
API_KEY_PATTERNS = {
    "Cloudinary": r"cloudinary://.*",
    "Firebase URL": r".*firebaseio\.com",
    "Slack Token": r"(xox[p|b|o|a]-[0-9]{12}-[0-9]{12}-[0-9]{12}-[a-z0-9]{32})",
    "RSA private key": r"-----BEGIN RSA PRIVATE KEY-----",
    "SSH (DSA) private key": r"-----BEGIN DSA PRIVATE KEY-----",
    "SSH (EC) private key": r"-----BEGIN EC PRIVATE KEY-----",
    "PGP private key block": r"-----BEGIN PGP PRIVATE KEY BLOCK-----",
    "Amazon AWS Access Key ID": r"AKIA[0-9A-Z]{16}",
    "Amazon MWS Auth Token": r"amzn\.mws\.[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}",
    "AWS API Key": r"AKIA[0-9A-Z]{16}",
    "Facebook Access Token": r"EAACEdEose0cBA[0-9A-Za-z]+",
    "Facebook OAuth": r"[f|F][a|A][c|C][e|E][b|B][o|O][o|O][k|K].*['|\"][0-9a-f]{32}['|\"]",
    "GitHub": r"[g|G][i|I][t|T][h|H][u|U][b|B].*['|\"][0-9a-zA-Z]{35,40}['|\"]",
    "Generic API Key": r"[a|A][p|P][i|I][_]?[k|K][e|E][y|Y].*['|\"][0-9a-zA-Z]{32,45}['|\"]",
    "Generic Secret": r"[s|S][e|E][c|C][r|R][e|E][t|T].*['|\"][0-9a-zA-Z]{32,45}['|\"]",
    "Google API Key": r"AIza[0-9A-Za-z\-_]{35}",
    "Google Cloud Platform API Key": r"AIza[0-9A-Za-z\-_]{35}",
    "Google Cloud Platform OAuth": r"[0-9]+-[0-9A-Za-z_]{32}\.apps\.googleusercontent\.com",
    "Google Drive API Key": r"AIza[0-9A-Za-z\-_]{35}",
    "Google Drive OAuth": r"[0-9]+-[0-9A-Za-z_]{32}\.apps\.googleusercontent\.com",
    "Google (GCP) Service-account": r'"type": "service_account"',
    "Google Gmail API Key": r"AIza[0-9A-Za-z\-_]{35}",
    "Google Gmail OAuth": r"[0-9]+-[0-9A-Za-z_]{32}\.apps\.googleusercontent\.com",
    "Google OAuth Access Token": r"ya29\.[0-9A-Za-z\-_]+",
    "Google YouTube API Key": r"AIza[0-9A-Za-z\-_]{35}",
    "Google YouTube OAuth": r"[0-9]+-[0-9A-Za-z_]{32}\.apps\.googleusercontent\.com",
    "Heroku API Key": r"[h|H][e|E][r|R][o|O][k|K][u|U].*[0-9A-F]{8}-[0-9A-F]{4}-[0-9A-F]{4}-[0-9A-F]{4}-[0-9A-F]{12}",
    "MailChimp API Key": r"[0-9a-f]{32}-us[0-9]{1,2}",
    "Mailgun API Key": r"key-[0-9a-zA-Z]{32}",
    "Password in URL": r"[a-zA-Z]{3,10}://[^/\s:@]{3,20}:[^/\s:@]{3,20}@.{1,100}[\"'\s]",
    "PayPal Braintree Access Token": r"access_token\$production\$[0-9a-z]{16}\$[0-9a-f]{32}",
    "Picatic API Key": r"sk_live_[0-9a-z]{32}",
    "Slack Webhook": r"https://hooks.slack.com/services/T[a-zA-Z0-9_]{8}/B[a-zA-Z0-9_]{8}/[a-zA-Z0-9_]{24}",
    "Stripe API Key": r"sk_live_[0-9a-zA-Z]{24}",
    "Stripe Restricted API Key": r"rk_live_[0-9a-zA-Z]{24}",
    "Square Access Token": r"sq0atp-[0-9A-Za-z\-_]{22}",
    "Square OAuth Secret": r"sq0csp-[0-9A-Za-z\-_]{43}",
    "Twilio API Key": r"SK[0-9a-fA-F]{32}",
    "Twitter Access Token": r"[t|T][w|W][i|I][t|T][t|T][e|E][r|R].*[1-9][0-9]+-[0-9a-zA-Z]{40}",
    "Twitter OAuth": r"[t|T][w|W][i|I][t|T][t|T][e|E][r|R].*['|\"][0-9a-zA-Z]{35,44}['|\"]",
    "MercadoPago Access Token": r"APP_USR-[0-9a-zA-Z\-]{16,64}",
    "MercadoPago Public Key": r"APP_USR-[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}",
    "MercadoPago Test Token": r"TEST-[0-9a-zA-Z\-]{16,64}"
}

class CredentialFinder:
    def __init__(self, engine_type: SearchEngineType = None):
        """
        Initialize CredentialFinder with support for multiple search engines
        
        Args:
            engine_type: Type of search engine to use (Google or DuckDuckGo)
                        If None, will try to use Google first, fallback to DuckDuckGo
        """
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        # Initialize search manager
        self.search_manager = create_search_manager()
        
        # Optional: wrap with EngineAwareSearchManager for per-engine query optimization
        try:
            self.engine_aware_manager = EngineAwareSearchManager(self.search_manager)
        except Exception:
            self.engine_aware_manager = None
        
        # Global search scope and filtering configuration (user-adjustable)
        # -----------------------------------------------------------------
        # default_num_results: cuántos resultados por consulta y por motor
        self.default_num_results = int(os.getenv("CRED_FINDER_RESULTS_PER_QUERY", "5"))
        
        # target_sites: dominios principales donde queremos buscar credenciales
        # El usuario puede modificar esta lista desde el menú de configuración.
        self.target_sites = [
            "github.com",
            "gitlab.com",
            "bitbucket.org",
            "gist.github.com",
        ]
        
        # Filtros globales avanzados (se aplican después de cada búsqueda)
        self.global_filters = {
            # Si se define, solo se mostrarán resultados que contengan alguno de estos dominios
            "allowed_domains": [],
            # Dominios que se filtrarán por defecto (docs, Q&A, etc.)
            "blocked_domains": [
                "stackoverflow.com",
                "stackexchange.com",
                "superuser.com",
                "serverfault.com",
                "quora.com",
                "docs.github.com",
                "github.community",
            ],
            # Extensiones de archivo requeridas en la URL (sin el punto), por ej: ["env", "yml", "json"]
            "required_filetypes": [],
            # Umbrales opcionales de calidad y riesgo (0.0 - 1.0)
            "min_quality_score": None,
            "min_risk_score": None,
            # Si se debe hacer análisis profundo de cada URL (puede ser lento)
            "analyze_urls": True,
        }
        
        # Permite activar/desactivar el uso de filtros avanzados
        self.use_advanced_filters = True
        
        # Set search engine
        self.set_search_engine(engine_type)
        
        # Legacy support for Google API (will be used as fallback)
        self.api_key = os.getenv('API_KEY_GOOGLE')
        self.engine_id = os.getenv('SEARCH_ENGINE_ID')
        
        print(f"🔍 CredentialFinder initialized with {self.current_engine_type.value if self.current_engine_type else 'auto-select'} engine")
        
        # Initialize query optimizer
        try:
            self.query_optimizer = QueryOptimizer()
            print("✅ Query optimizer enabled")
        except ImportError:
            self.query_optimizer = None
            print("⚠️  Query optimizer not available")
    
    def set_search_engine(self, engine_type: SearchEngineType = None):
        """
        Set the search engine to use
        
        Args:
            engine_type: Type of search engine, or None for auto-selection
        """
        if engine_type:
            try:
                self.search_manager.set_engine(engine_type)
                self.current_engine_type = engine_type
            except ValueError as e:
                print(f"⚠️  Could not set {engine_type.value} engine: {e}")
                self._auto_select_engine()
        else:
            self._auto_select_engine()
    
    def _auto_select_engine(self):
        """
        Automatically select the best available search engine
        """
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

        # Show warning if no Google/Serper engine
        if self.current_engine_type not in (SearchEngineType.GOOGLE, SearchEngineType.SERPER_GOOGLE):
            print("⚠️  Using non-Google engine (Google/Serper not available)")
    
    def _optimize_query(self, query: str) -> str:
        """
        Optimize query using query optimizer if available
        
        Args:
            query: Original search query
        
        Returns:
            Optimized query
        """
        if not self.query_optimizer or not self.current_engine_type:
            return query
        
        optimized_query = self.query_optimizer.optimize_query(query, self.current_engine_type)
        
        if optimized_query != query:
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
    
    def get_search_engine_info(self) -> dict:
        """
        Get information about the current search engine

        Returns:
            Dictionary with engine information
        """
        available_engines = self.search_manager.get_available_engines()
        return {
            'engine_type': self.current_engine_type.value if self.current_engine_type else None,
            'available_engines': [e.value for e in available_engines],
            'google_api_available': bool(self.api_key and self.engine_id),
            'serp_api_available': bool(os.getenv('SERP_API_KEY')),
            'serper_api_available': bool(os.getenv('SERPER_API_KEY')),
            'selenium_available': SearchEngineType.SELENIUM_GOOGLE in available_engines,
            'query_optimizer_available': self.query_optimizer is not None
        }
    
    def search_with_engine(self, query: str, num: int = 10, **kwargs):
        """
        Perform search using the current search engine
        
        Args:
            query: Search query
            num: Number of results
            **kwargs: Additional search parameters
        
        Returns:
            Standardized search results
        """
        return self.search_manager.search(query, num, **kwargs)
        
    def search(self, query: str, num: int = 10, **kwargs):
        """
        Perform search using the current search engine with query optimization
        
        Args:
            query: Search query
            num: Number of results
            **kwargs: Additional search parameters
        
        Returns:
            Standardized search results
        """
        # Analyze query compatibility
        compatibility = self._analyze_query_compatibility(query)
        if compatibility.get('recommendation') != 'Query optimizer not available':
            print(f"💡 Query optimization: {compatibility.get('recommendation', 'No recommendation')}")
        
        # Optimize query
        optimized_query = self._optimize_query(query)
        
        try:
            return self.search_with_engine(optimized_query, num, **kwargs)
        except Exception as e:
            print(f"❌ Error in search: {e}")
            
            # Fallback to Google API if available
            if self.api_key and self.engine_id:
                print("🔄 Falling back to Google Custom Search API...")
                return self._google_api_search(optimized_query, num)
            
            return []
    
    def _google_api_search(self, query: str, num: int = 10):
        """
        Fallback to direct Google Custom Search API
        """
        url = f'https://www.googleapis.com/customsearch/v1?key={self.api_key}&cx={self.engine_id}&q={query}&num={num}'
        
        try:
            response = self.session.get(url)
            response.raise_for_status()
            data = response.json()
            items = data.get('items', [])
            
            # Convert to standardized format
            results = []
            for item in items:
                results.append({
                    'title': item.get('title', 'N/A'),
                    'link': item.get('link', 'N/A'),
                    'snippet': item.get('snippet', 'N/A'),
                    'display_link': item.get('displayLink', 'N/A'),
                    'source': 'google_api'
                })
            
            return results
        except requests.RequestException as e:
            print(f"❌ Error in Google API search: {e}")
            return []
    
    def github_search(self, query: str):
        """
        Search GitHub for sensitive files using current search engine
        
        Args:
            query: Search query
        
        Returns:
            List of GitHub-related results
        """
        search_queries = [
            f'site:github.com {query}',
            f'site:raw.githubusercontent.com {query}',
            f'site:githubusercontent.com {query}'
        ]
        
        all_results = []
        for search_query in search_queries:
            print(f"  🔍 Searching: {search_query}")
            results = self.search(search_query, 10)
            all_results.extend(results)
            time.sleep(1)  # Rate limiting
            
        return all_results
    
    def cross_engine_search(self, query: str, num: int = 10) -> dict:
        """
        Search using multiple engines and return comparison results.
        If EngineAwareSearchManager is available, use per-engine optimized queries.
        """
        print(f"🔍 Cross-engine search for: {query}")
        
        # If we have an engine-aware manager, use it to optimize queries per engine
        if getattr(self, "engine_aware_manager", None):
            # Per-engine optimized search
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
                'query': query,
                'total_unique_urls': len(all_urls),
                'results_by_engine': results_by_engine,
                'overlap_percentage': overlaps,
                'engines_tested': list(results_by_engine.keys())
            }
        else:
            # Fallback to the manager's built-in comparison (single query for all engines)
            comparison = self.search_manager.compare_results(query, num)
        
        # Get best combined results from all engines
        results_list = list(comparison['results_by_engine'].values())
        best_results = SearchResultComparator.get_best_results(results_list, top_n=num)
        
        # Add quality scores to original results
        for engine_type, results in comparison['results_by_engine'].items():
            for result in results:
                result['quality_score'] = SearchResultComparator.calculate_quality_score([result])
        
        comparison['best_combined'] = best_results
        comparison['total_quality_score'] = SearchResultComparator.calculate_quality_score(best_results)
        
        return comparison
    
    def find_env_files(self):
        """
        Search for .env files using current search engine
        
        Returns:
            List of .env file results
        """
        # Plantillas base pensadas para GitHub que luego se adaptan a otros sitios
        base_queries = [
            'site:github.com ".env" filetype:env',
            'site:github.com "DB_PASSWORD" filetype:env',
            'site:github.com "API_KEY" filetype:env',
            'site:github.com "SECRET_KEY" filetype:env',
        ]
        generic_queries = [
            'inurl:.env "password"',
            'inurl:.env "database"',
        ]
        
        # Expandimos a todos los dominios configurados por el usuario
        sites = getattr(self, "target_sites", None) or ["github.com"]
        queries = []
        for site in sites:
            for q in base_queries:
                queries.append(q.replace("site:github.com", f"site:{site}"))
        # Las queries genéricas se añaden una sola vez
        queries.extend(generic_queries)
        
        print(f"🔍 Buscando archivos .env con {self.current_engine_type.value}...")
        results = []
        for query in queries:
            print(f"  Consulta: {query}")
            results.extend(self.search(query, self.default_num_results))
            time.sleep(1)
            
        return self.apply_advanced_filters(results, ['env', 'database', 'password', 'secret', 'key'])
    
    def find_env_files_cross_engine(self):
        """
        Search for .env files across multiple engines
        
        Returns:
            Cross-engine comparison results
        """
        print("🔍 Cross-engine search for .env files...")
        
        # Main query for .env files
        query = 'site:github.com ".env" filetype:env OR "password" OR "database"'
        comparison = self.cross_engine_search(query, num=10)
        
        return comparison
    
    def find_config_files(self):
        """
        Search for configuration files using current search engine
        
        Returns:
            List of configuration file results
        """
        base_queries = [
            'site:github.com "config.js" "password"',
            'site:github.com "config.json" "password"',
            'site:github.com "settings.json" "api_key"',
            'site:github.com "webpack.config.js" "env"',
            'site:github.com "config.php" "db_password"'
        ]
        
        sites = getattr(self, "target_sites", None) or ["github.com"]
        queries = []
        for site in sites:
            for q in base_queries:
                queries.append(q.replace("site:github.com", f"site:{site}"))
        
        print(f"🔍 Buscando archivos de configuración con {self.current_engine_type.value}...")
        results = []
        for query in queries:
            print(f"  Consulta: {query}")
            results.extend(self.search(query, self.default_num_results))
            time.sleep(1)
            
        return self.apply_advanced_filters(results, ['config', 'password', 'key', 'secret'])
    
    def find_credentials(self):
        """
        Search for various credential patterns using current search engine
        
        Returns:
            List of credential-related results
        """
        base_queries = [
            'site:github.com "password" "admin"',
            'site:github.com "api_key" "secret"',
            'site:github.com "db_password" "mysql"',
            'site:github.com "private_key" "-----BEGIN"',
            'site:github.com "access_token" "oauth"',
            'site:github.com "AWS_ACCESS_KEY_ID"',
            'site:github.com "STRIPE_SECRET_KEY"'
        ]
        
        # Permitir más fuentes que solo GitHub (gitlab, bitbucket, pastebin, etc.)
        sites = getattr(self, "target_sites", None) or ["github.com"]
        queries = []
        for site in sites:
            for q in base_queries:
                queries.append(q.replace("site:github.com", f"site:{site}"))
        
        print(f"🔍 Buscando credenciales con {self.current_engine_type.value}...")
        results = []
        for query in queries:
            print(f"  Consulta: {query}")
            results.extend(self.search(query, self.default_num_results))
            time.sleep(1)
            
        return self.apply_advanced_filters(results, ['password', 'key', 'secret', 'token'])
    
    def find_api_endpoints(self):
        """
        Search for API endpoints using current search engine
        
        Returns:
            List of API endpoint results
        """
        base_queries = [
            'site:github.com "api/v1" "endpoint"',
            'site:github.com "/api/" "token"',
            'site:github.com "swagger" "api"',
            'site:github.com "postman" "collection"',
            'site:github.com "graphql" "endpoint"'
        ]
        
        sites = getattr(self, "target_sites", None) or ["github.com"]
        queries = []
        for site in sites:
            for q in base_queries:
                queries.append(q.replace("site:github.com", f"site:{site}"))
        
        print(f"🔍 Buscando endpoints de API con {self.current_engine_type.value}...")
        results = []
        for query in queries:
            print(f"  Consulta: {query}")
            results.extend(self.search(query, self.default_num_results))
            time.sleep(1)
            
        return self.apply_advanced_filters(results, ['api', 'endpoint', 'token'])
    
    def find_openai_api_keys(self):
        """
        Search for OpenAI API keys using GitHub search syntax
        
        Returns:
            List of OpenAI API key results
        """
        # GitHub Search Syntax for OpenAI API keys
        file_extensions = "xml OR json OR properties OR sql OR txt OR log OR tmp OR backup OR bak OR enc OR yml OR yaml OR toml OR ini OR config OR conf OR cfg OR env OR envrc OR prod OR secret OR private OR key"
        key_names = "access_key OR secret_key OR access_token OR api_key OR apikey OR api_secret OR apiSecret OR app_secret OR application_key OR app_key OR appkey OR auth_token OR authsecret"
        
        queries = [
            f'(path:*.{file_extensions}) AND ({key_names}) AND ("sk-" AND (openai OR gpt))',
            f'(path:*.{file_extensions}) AND ({key_names}) AND (/sk-[a-zA-Z0-9]{{48}}/ AND (openai OR gpt))'
        ]
        
        # Also search specific sites
        sites = getattr(self, "target_sites", None) or ["github.com"]
        site_specific_queries = []
        for site in sites:
            site_specific_queries.extend([
                f'site:{site} "sk-" (openai OR gpt)',
                f'site:{site} "OpenAI" "api_key"',
                f'site:{site} "openai_api_key"'
            ])
        
        all_queries = queries + site_specific_queries
        
        print(f"🔍 Buscando API keys de OpenAI con {self.current_engine_type.value}...")
        results = []
        for query in all_queries:
            print(f"  Consulta: {query}")
            results.extend(self.search(query, self.default_num_results))
            time.sleep(1)
            
        return self.apply_advanced_filters(results, ['openai', 'gpt', 'sk-', 'api_key'])
    
    def find_github_tokens(self):
        """
        Search for GitHub OAuth/App/Personal/Refresh Access Tokens
        
        Returns:
            List of GitHub token results
        """
        # GitHub Search Syntax for GitHub tokens
        file_extensions = "xml OR json OR properties OR sql OR txt OR log OR tmp OR backup OR bak OR enc OR yml OR yaml OR toml OR ini OR config OR conf OR cfg OR env OR envrc OR prod OR secret OR private OR key"
        key_names = "access_key OR secret_key OR access_token OR api_key OR apikey OR api_secret OR apiSecret OR app_secret OR application_key OR app_key OR appkey OR auth_token OR authsecret"
        
        queries = [
            f'(path:*.{file_extensions}) AND ({key_names}) AND (("ghp_" OR "gho_" OR "ghu_" OR "ghs_" OR "ghr_") AND (Github OR OAuth))'
        ]
        
        # Site-specific searches
        sites = getattr(self, "target_sites", None) or ["github.com"]
        site_specific_queries = []
        for site in sites:
            site_specific_queries.extend([
                f'site:{site} ("ghp_" OR "gho_" OR "ghu_" OR "ghs_" OR "ghr_")',
                f'site:{site} "github_token"',
                f'site:{site} "github_oauth"'
            ])
        
        all_queries = queries + site_specific_queries
        
        print(f"🔍 Buscando tokens de GitHub con {self.current_engine_type.value}...")
        results = []
        for query in all_queries:
            print(f"  Consulta: {query}")
            results.extend(self.search(query, self.default_num_results))
            time.sleep(1)
            
        return self.apply_advanced_filters(results, ['github', 'ghp_', 'gho_', 'ghu_', 'ghs_', 'ghr_', 'oauth'])
    
    def find_slack_tokens(self):
        """
        Search for Slack tokens
        
        Returns:
            List of Slack token results
        """
        # GitHub Search Syntax for Slack tokens
        file_extensions = "xml OR json OR properties OR sql OR txt OR log OR tmp OR backup OR bak OR enc OR yml OR yaml OR toml OR ini OR config OR conf OR cfg OR env OR envrc OR prod OR secret OR private OR key"
        key_names = "access_key OR secret_key OR access_token OR api_key OR apikey OR api_secret OR apiSecret OR app_secret OR application_key OR app_key OR appkey OR auth_token OR authsecret"
        
        queries = [
            f'(path:*.{file_extensions}) AND ({key_names}) AND (xox AND Slack)'
        ]
        
        # Site-specific searches
        sites = getattr(self, "target_sites", None) or ["github.com"]
        site_specific_queries = []
        for site in sites:
            site_specific_queries.extend([
                f'site:{site} "xox" Slack',
                f'site:{site} "slack_token"',
                f'site:{site} "slack_api"'
            ])
        
        all_queries = queries + site_specific_queries
        
        print(f"🔍 Buscando tokens de Slack con {self.current_engine_type.value}...")
        results = []
        for query in all_queries:
            print(f"  Consulta: {query}")
            results.extend(self.search(query, self.default_num_results))
            time.sleep(1)
            
        return self.apply_advanced_filters(results, ['slack', 'xox', 'token'])
    
    def find_google_api_keys(self):
        """
        Search for Google API keys
        
        Returns:
            List of Google API key results
        """
        # GitHub Search Syntax for Google API keys
        file_extensions = "xml OR json OR properties OR sql OR txt OR log OR tmp OR backup OR bak OR enc OR yml OR yaml OR toml OR ini OR config OR conf OR cfg OR env OR envrc OR prod OR secret OR private OR key"
        key_names = "access_key OR secret_key OR access_token OR api_key OR apikey OR api_secret OR apiSecret OR app_secret OR application_key OR app_key OR appkey OR auth_token OR authsecret"
        
        queries = [
            f'(path:*.{file_extensions}) AND ({key_names}) AND (AIza AND Google)'
        ]
        
        # Site-specific searches
        sites = getattr(self, "target_sites", None) or ["github.com"]
        site_specific_queries = []
        for site in sites:
            site_specific_queries.extend([
                f'site:{site} "AIza" Google',
                f'site:{site} "google_api_key"',
                f'site:{site} "google_api"'
            ])
        
        all_queries = queries + site_specific_queries
        
        print(f"🔍 Buscando API keys de Google con {self.current_engine_type.value}...")
        results = []
        for query in all_queries:
            print(f"  Consulta: {query}")
            results.extend(self.search(query, self.default_num_results))
            time.sleep(1)
            
        return self.apply_advanced_filters(results, ['google', 'AIza', 'api_key'])
    
    def find_square_tokens(self):
        """
        Search for Square OAuth/access tokens
        
        Returns:
            List of Square token results
        """
        # GitHub Search Syntax for Square tokens
        file_extensions = "xml OR json OR properties OR sql OR txt OR log OR tmp OR backup OR bak OR enc OR yml OR yaml OR toml OR ini OR config OR conf OR cfg OR env OR envrc OR prod OR secret OR private OR key"
        key_names = "access_key OR secret_key OR access_token OR api_key OR apikey OR api_secret OR apiSecret OR app_secret OR application_key OR app_key OR appkey OR auth_token OR authsecret"
        
        queries = [
            f'(path:*.{file_extensions}) AND ({key_names}) AND (("sq0atp-" OR "sq0csp-") AND (square OR OAuth))'
        ]
        
        # Site-specific searches
        sites = getattr(self, "target_sites", None) or ["github.com"]
        site_specific_queries = []
        for site in sites:
            site_specific_queries.extend([
                f'site:{site} ("sq0atp-" OR "sq0csp-")',
                f'site:{site} "square_token"',
                f'site:{site} "square_oauth"'
            ])
        
        all_queries = queries + site_specific_queries
        
        print(f"🔍 Buscando tokens de Square con {self.current_engine_type.value}...")
        results = []
        for query in all_queries:
            print(f"  Consulta: {query}")
            results.extend(self.search(query, self.default_num_results))
            time.sleep(1)
            
        return self.apply_advanced_filters(results, ['square', 'sq0atp', 'sq0csp', 'oauth'])
    
    def find_shopify_secrets(self):
        """
        Search for Shopify shared secret, access token, private/custom app access token
        
        Returns:
            List of Shopify secret results
        """
        # GitHub Search Syntax for Shopify secrets
        file_extensions = "xml OR json OR properties OR sql OR txt OR log OR tmp OR backup OR bak OR enc OR yml OR yaml OR toml OR ini OR config OR conf OR cfg OR env OR envrc OR prod OR secret OR private OR key"
        key_names = "access_key OR secret_key OR access_token OR api_key OR apikey OR api_secret OR apiSecret OR app_secret OR application_key OR app_key OR appkey OR auth_token OR authsecret"
        
        queries = [
            f'(path:*.{file_extensions}) AND ({key_names}) AND (("shpss_" OR "shpat_" OR "shpca_" OR "shppa_") AND "Shopify")'
        ]
        
        # Site-specific searches
        sites = getattr(self, "target_sites", None) or ["github.com"]
        site_specific_queries = []
        for site in sites:
            site_specific_queries.extend([
                f'site:{site} ("shpss_" OR "shpat_" OR "shpca_" OR "shppa_")',
                f'site:{site} "shopify_secret"',
                f'site:{site} "shopify_access_token"'
            ])
        
        all_queries = queries + site_specific_queries
        
        print(f"🔍 Buscando secretos de Shopify con {self.current_engine_type.value}...")
        results = []
        for query in all_queries:
            print(f"  Consulta: {query}")
            results.extend(self.search(query, self.default_num_results))
            time.sleep(1)
            
        return self.apply_advanced_filters(results, ['shopify', 'shpss', 'shpat', 'shpca', 'shppa'])
    
    def find_mercadopago_tokens(self):
        """
        Search for MercadoPago access tokens and public keys
        
        Returns:
            List of MercadoPago token results
        """
        # GitHub Search Syntax for MercadoPago tokens
        file_extensions = "xml OR json OR properties OR sql OR txt OR log OR tmp OR backup OR bak OR enc OR yml OR yaml OR toml OR ini OR config OR conf OR cfg OR env OR envrc OR prod OR secret OR private OR key"
        key_names = "access_key OR secret_key OR access_token OR api_key OR apikey OR api_secret OR apiSecret OR app_secret OR application_key OR app_key OR appkey OR auth_token OR authsecret"
        
        queries = [
            f'(path:*.{file_extensions}) AND ({key_names}) AND (("APP_USR-" OR "TEST-") AND (MercadoPago OR Mercado))'
        ]
        
        # Site-specific searches
        sites = getattr(self, "target_sites", None) or ["github.com"]
        site_specific_queries = []
        for site in sites:
            site_specific_queries.extend([
                f'site:{site} ("APP_USR-" OR "TEST-") MercadoPago',
                f'site:{site} "MERCADOPAGO_ACCESS_TOKEN"',
                f'site:{site} "MERCADOPAGO_PUBLIC_KEY"',
                f'site:{site} "mercadopago" ("access_token" OR "public_key")'
            ])
        
        all_queries = queries + site_specific_queries
        
        print(f"🔍 Buscando tokens de MercadoPago con {self.current_engine_type.value}...")
        results = []
        for query in all_queries:
            print(f"  Consulta: {query}")
            results.extend(self.search(query, self.default_num_results))
            time.sleep(1)
            
        return self.apply_advanced_filters(results, ['mercadopago', 'mercado', 'APP_USR', 'TEST-', 'access_token', 'public_key'])
    
    def find_all_api_keys(self):
        """
        Search for API keys across all supported platforms
        
        Returns:
            Dictionary with results for each platform
        """
        print(f"🔍 Buscando API keys en todas las plataformas con {self.current_engine_type.value}...")
        
        results = {
            'openai': self.find_openai_api_keys(),
            'github': self.find_github_tokens(),
            'slack': self.find_slack_tokens(),
            'google': self.find_google_api_keys(),
            'square': self.find_square_tokens(),
            'shopify': self.find_shopify_secrets(),
            'mercadopago': self.find_mercadopago_tokens()
        }
        
        return results
    
    def find_all_api_keys_cross_engine(self):
        """
        Search for API keys across all supported platforms using cross-engine search
        
        Returns:
            Cross-engine comparison results for all platforms
        """
        print("🔍 Búsqueda multi-motor de API keys en todas las plataformas...")
        
        # Define queries for each platform
        platform_queries = {
            'openai': '("sk-" AND (openai OR gpt)) OR site:github.com "openai_api_key"',
            'github': '("ghp_" OR "gho_" OR "ghu_" OR "ghs_" OR "ghr_") OR site:github.com "github_token"',
            'slack': '(xox AND Slack) OR site:github.com "slack_token"',
            'google': '(AIza AND Google) OR site:github.com "google_api_key"',
            'square': '("sq0atp-" OR "sq0csp-") OR site:github.com "square_token"',
            'shopify': '("shpss_" OR "shpat_" OR "shpca_" OR "shppa_") OR site:github.com "shopify_secret"',
            'mercadopago': '("APP_USR-" OR "TEST-") OR site:github.com "MERCADOPAGO_ACCESS_TOKEN"'
        }
        
        all_results = {}
        
        for platform, query in platform_queries.items():
            print(f"\n🔍 Searching {platform.upper()} tokens with multiple engines...")
            try:
                results = self.cross_engine_search(query, num=self.default_num_results)
                all_results[platform] = results
                time.sleep(2)  # Rate limiting between platforms
            except Exception as e:
                print(f"❌ Error in {platform} search: {e}")
                all_results[platform] = {}
        
        return all_results
    
    def dork_search(self, custom_query: str, use_cross_engine: bool = False):
        """
        Perform custom Dork search using current search engine
        
        Args:
            custom_query: Custom search query
            use_cross_engine: Whether to use cross-engine search
        
        Returns:
            Search results (list or dict if cross-engine)
        """
        print(f"🔍 Ejecutando búsqueda Dork personalizada: {custom_query}")
        
        if use_cross_engine:
            return self.cross_engine_search(custom_query, num=self.default_num_results)
        else:
            results = self.search(custom_query, self.default_num_results)
            # Usamos filtros avanzados genéricos orientados a credenciales / config
            return self.apply_advanced_filters(results, ['password', 'key', 'secret', 'token', 'config'])
    
    def _infer_filetype_from_url(self, url: str) -> str:
        """
        Infer a simple filetype/extension from a URL.
        Used for post-processing and basic risk scoring.
        """
        if not url:
            return ""
        lowered = url.lower()
        for ext in [".env", ".json", ".yml", ".yaml", ".ini", ".config", ".cfg", ".php", ".txt", ".log"]:
            if ext in lowered:
                return ext.lstrip(".")
        # crude fallback based on last dot
        if "." in lowered.rsplit("/", 1)[-1]:
            return lowered.rsplit(".", 1)[-1][:10]
        return ""
    
    def _compute_risk_score(self, result: Dict[str, str]) -> float:
        """
        Compute a simple risk score (0-1) for a single standardized result.
        
        Factors considered:
        - Filetype appears sensitive (.env, .config, .php, etc.)
        - Presence of credential-related keywords in title/snippet
        - Domain sensitivity (non-github domains get a slight bump)
        """
        url = result.get("link", "") or ""
        title = (result.get("title", "") or "").lower()
        snippet = (result.get("snippet", "") or "").lower()
        
        score = 0.0
        factors = 3
        
        # Factor 1: sensitive filetypes
        filetype = self._infer_filetype_from_url(url)
        sensitive_types = {"env", "config", "yml", "yaml", "ini", "cfg", "php", "json"}
        if filetype in sensitive_types:
            score += 1.0
        
        # Factor 2: credential keywords
        text = f"{title} {snippet}"
        cred_keywords = ["password", "pass=", "passwd", "secret", "token", "api_key", "access_key", "private key"]
        if any(k in text for k in cred_keywords):
            score += 1.0
        
        # Factor 3: non-github domains get a small bump (more likely to be real exposure)
        if url and "github.com" not in url and "gitlab.com" not in url:
            score += 1.0
        
        return score / factors if factors else 0.0
    
    def filter_results(self, results: List[Dict[str, str]], keywords: List[str]) -> List[Dict[str, str]]:
        """
        Basic keyword-based filtering over standardized results.
        Also annotates results with a computed risk_score for later use.
        """
        filtered: List[Dict[str, str]] = []
        for result in results or []:
            title = (result.get('title', '') or '').lower()
            snippet = (result.get('snippet', '') or '').lower()
            link = (result.get('link', '') or '').lower()
            
            text = f"{title} {snippet} {link}"
            if any(keyword in text for keyword in keywords):
                # Attach risk_score so it can be reused later (display, extra filters, etc.)
                result['risk_score'] = self._compute_risk_score(result)
                filtered.append(result)
        
        return filtered
    
    def filter_results_advanced(
        self,
        results: List[Dict[str, str]],
        keywords: Optional[List[str]] = None,
        allowed_domains: Optional[List[str]] = None,
        blocked_domains: Optional[List[str]] = None,
        required_filetypes: Optional[List[str]] = None,
        min_quality_score: Optional[float] = None,
        min_risk_score: Optional[float] = None,
    ) -> List[Dict[str, str]]:
        """
        Advanced filtering over standardized results.
        
        Args:
            results: List of standardized results
            keywords: Optional list of keywords to match in title/snippet/link
            allowed_domains: If provided, only results whose URL contains at least one of these
            blocked_domains: Domains to exclude from results
            required_filetypes: List of file extensions (without dot) required in URL
            min_quality_score: Minimum quality_score (if present on result)
            min_risk_score: Minimum risk_score (will be computed if absent)
        """
        if keywords:
            base = self.filter_results(results, keywords)
        else:
            base = results or []
        
        filtered: List[Dict[str, str]] = []
        for result in base:
            url = result.get("link", "") or ""
            lowered_url = url.lower()
            
            # Domain filters
            if allowed_domains:
                if not any(dom.lower() in lowered_url for dom in allowed_domains):
                    continue
            if blocked_domains:
                if any(dom.lower() in lowered_url for dom in blocked_domains):
                    continue
            
            # Filetype filters
            if required_filetypes:
                ft = self._infer_filetype_from_url(url)
                if not ft or ft.lower() not in [f.lower() for f in required_filetypes]:
                    continue
            
            # Quality score
            if min_quality_score is not None:
                q = result.get("quality_score")
                if q is None or q < min_quality_score:
                    continue
            
            # Risk score (compute if missing)
            if "risk_score" not in result:
                result["risk_score"] = self._compute_risk_score(result)
            if min_risk_score is not None and result["risk_score"] < min_risk_score:
                continue
            
            filtered.append(result)
        
        return filtered
    
    def apply_advanced_filters(self, results: List[Dict[str, str]], base_keywords: List[str]) -> List[Dict[str, str]]:
        """
        Wrapper que aplica los filtros avanzados globales definidos en la instancia.
        
        Si self.use_advanced_filters es False, solo aplica un filtrado básico
        por palabras clave. Si es True, utiliza filter_results_advanced con
        dominios permitidos/bloqueados, extensiones y umbrales.
        """
        # Si el usuario desactiva los filtros avanzados, usamos el filtrado simple
        if not getattr(self, "use_advanced_filters", True):
            return self.filter_results(results, base_keywords)
        
        gf = getattr(self, "global_filters", {}) or {}
        
        return self.filter_results_advanced(
            results,
            keywords=base_keywords,
            allowed_domains=gf.get("allowed_domains") or None,
            blocked_domains=gf.get("blocked_domains") or None,
            required_filetypes=gf.get("required_filetypes") or None,
            min_quality_score=gf.get("min_quality_score"),
            min_risk_score=gf.get("min_risk_score"),
        )
    
    def analyze_url(self, url):
        """Analizar una URL en busca de información sensible potencial usando patrones regex avanzados"""
        try:
            response = self.session.get(url, timeout=10)
            content = response.text
            
            found_credentials = []
            
            # Usar los patrones regex avanzados del diccionario global
            for key_type, pattern in API_KEY_PATTERNS.items():
                try:
                    matches = re.findall(pattern, content, re.IGNORECASE | re.MULTILINE)
                    if matches:
                        for match in matches:
                            found_credentials.append({
                                'type': key_type,
                                'value': match if isinstance(match, str) else str(match),
                                'url': url
                            })
                except re.error:
                    continue
            
            return found_credentials
        except Exception as e:
            print(f"Error al analizar la URL {url}: {e}")
            return []
    
    def scan_content_for_secrets(self, content: str) -> List[Dict[str, str]]:
        """
        Escanear contenido de texto en busca de API keys y secretos usando patrones regex.
        
        Args:
            content: Texto a escanear
        
        Returns:
            Lista de secretos encontrados con tipo y valor
        """
        found_secrets = []
        
        for key_type, pattern in API_KEY_PATTERNS.items():
            try:
                matches = re.findall(pattern, content, re.IGNORECASE | re.MULTILINE)
                if matches:
                    for match in matches:
                        found_secrets.append({
                            'type': key_type,
                            'value': match if isinstance(match, str) else str(match)
                        })
            except re.error:
                continue
        
        return found_secrets
    
    def get_supported_secret_types(self) -> List[str]:
        """
        Obtener lista de tipos de secretos soportados para detección.
        
        Returns:
            Lista de nombres de tipos de secretos
        """
        return list(API_KEY_PATTERNS.keys())
    
    def save_results(self, results, filename):
        """Guardar resultados en un archivo JSON"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        print(f"💾 Resultados guardados en {filename}")
    
    def display_results(self, results, category, is_cross_engine: bool = False):
        """
        Display search results in a formatted manner
        
        Args:
            results: Search results (list or dict for cross-engine)
            category: Category name for display
            is_cross_engine: Whether results are from cross-engine search
        """
        if is_cross_engine:
            # Handle cross-engine results
            self._display_cross_engine_results(results, category)
        else:
            # Handle regular results
            self._display_standard_results(results, category)
    
    def _display_standard_results(self, results, category):
        """Display standard search results"""
        if not results:
            print(f"❌ No se encontraron resultados para {category}")
            return
             
        print(f"\n📊 Resultados de {category} ({len(results)} encontrados):")
        print(f"🔍 Engine: {self.current_engine_type.value if self.current_engine_type else 'N/A'}")
        print("=" * 80)
        
        for i, result in enumerate(results, 1):
            # Ensure risk_score is available for display
            if "risk_score" not in result:
                try:
                    result["risk_score"] = self._compute_risk_score(result)
                except Exception:
                    result["risk_score"] = 0.0
            
            print(f"\n{i}. Título: {result.get('title', 'N/A')}")
            print(f"   URL: {result.get('link', 'N/A')}")
            print(f"   Fragmento: {result.get('snippet', 'N/A')[:150]}...")
            
            # Show quality score if available
            if 'quality_score' in result:
                print(f"   📈 Quality Score: {result['quality_score']:.2f}")
            
            # Show risk score
            if 'risk_score' in result:
                print(f"   ⚠️ Risk Score: {result['risk_score']:.2f}")
            
            # Show source if available
            if 'source' in result:
                print(f"   📍 Source: {result['source']}")
            
            # Try to analyze URL for credentials (optional, puede ser MUY lento con muchos resultados)
            credentials = []
            analyze_flag = getattr(self, "global_filters", {}).get("analyze_urls", True)
            
            # Para evitar cuelgues, limitamos el análisis profundo a las primeras N URLs
            MAX_DEEP_ANALYSIS = 20
            if analyze_flag and i <= MAX_DEEP_ANALYSIS:
                credentials = self.analyze_url(result.get('link', ''))
            elif analyze_flag and i == MAX_DEEP_ANALYSIS + 1:
                # Solo avisamos una vez que dejamos de analizar en profundidad
                print(f"   ⏱️ Se alcanzó el límite de análisis profundo ({MAX_DEEP_ANALYSIS} URLs).")
                print("      El resto de las URLs se muestran sin escaneo de contenido para evitar cuelgues.")
            
            if credentials:
                print(f"   🔑 Secretos encontrados: {len(credentials)}")
                for cred in credentials[:5]:  # Show first 5
                    cred_type = cred.get('type', 'Unknown')
                    cred_value = cred.get('value', '')
                    # Truncar valores largos para seguridad
                    if len(cred_value) > 50:
                        display_value = cred_value[:25] + "..." + cred_value[-10:]
                    else:
                        display_value = cred_value
                    print(f"      - [{cred_type}]: {display_value}")
            
            print("-" * 60)
    
    def _display_cross_engine_results(self, results, category):
        """Display cross-engine search results"""
        if not results:
            print(f"❌ No se encontraron resultados para {category}")
            return
        
        print(f"\n🔍 Resultados multi‑motor para {category}")
        print("=" * 80)
        
        # Resumen
        print(f"📊 Total de URLs únicas: {results.get('total_unique_urls', 0)}")
        print(f"🎯 Puntuación de calidad global: {results.get('total_quality_score', 0):.2f}")
        
        engines = results.get('engines_tested', [])
        engine_labels = []
        for e in engines:
            if hasattr(e, "value"):
                engine_labels.append(e.value)
            else:
                engine_labels.append(str(e))
        if engine_labels:
            print(f"🔍 Motores probados: {', '.join(engine_labels)}")
        
        # Mostrar porcentajes de solapamiento
        overlap = results.get('overlap_percentage', {})
        if overlap:
            print(f"\n🔗 Análisis de solapamiento:")
            for engine, percentage in overlap.items():
                label = engine.value if hasattr(engine, "value") else str(engine)
                print(f"   {label}: {percentage:.1%}")
        
        # Show best combined results
        if 'best_combined' in results:
            print(f"\n🏆 Top Combined Results:")
            print("-" * 60)
            best_results = results['best_combined']
            for i, result in enumerate(best_results[:10], 1):  # Show top 10
                print(f"\n{i}. {result.get('title', 'N/A')}")
                print(f"   URL: {result.get('link', 'N/A')}")
                print(f"   Quality: {result.get('quality_score', 0):.2f}")
                print(f"   Snippet: {result.get('snippet', 'N/A')[:100]}...")
        
        # Show results by engine
        results_by_engine = results.get('results_by_engine', {})
        for engine_type, engine_results in results_by_engine.items():
            if engine_results:
                print(f"\n🔍 Results from {engine_type.value} ({len(engine_results)} results):")
                print("-" * 40)
                for i, result in enumerate(engine_results[:5], 1):  # Show top 5 per engine
                    print(f"{i}. {result.get('title', 'N/A')[:60]}...")
                    print(f"   {result.get('link', 'N/A')[:80]}...")
    
    def display_engine_comparison(self, comparison_results):
        """Display detailed engine comparison results"""
        if not comparison_results:
            return
        
        print(f"\n🔍 Engine Comparison Analysis")
        print("=" * 80)
        
        # Get results by engine
        results_by_engine = comparison_results.get('results_by_engine', {})
        
        if len(results_by_engine) < 2:
            print("❌ Need at least 2 engines for comparison")
            return
        
        # Calculate quality scores per engine
        engine_scores = {}
        for engine_type, results in results_by_engine.items():
            score = SearchResultComparator.calculate_quality_score(results)
            engine_scores[engine_type] = score
        
        # Display engine rankings
        sorted_engines = sorted(engine_scores.items(), key=lambda x: x[1], reverse=True)
        
        print(f"🏆 Engine Quality Ranking:")
        for i, (engine_type, score) in enumerate(sorted_engines, 1):
            print(f"{i}. {engine_type.value.title()}: {score:.2f}")
        
        # Find duplicates
        results_list = list(results_by_engine.values())
        duplicates = SearchResultComparator.find_duplicates(results_list)
        
        if duplicates:
            print(f"\n🔗 Common Results (found by multiple engines): {len(duplicates)}")
            # Show top duplicates
            for i, (url, engines) in enumerate(list(duplicates.items())[:5], 1):
                engine_names = [list(results_by_engine.keys())[e] for e in engines]
                print(f"{i}. {url[:60]}...")
                print(f"   Found by: {', '.join([e.value for e in engine_names])}")
        else:
            print(f"\n🔍 No common results found between engines")
        
        # Overall assessment
        best_engine = sorted_engines[0]
        print(f"\n✅ Best performing engine: {best_engine[0].value.title()} (score: {best_engine[1]:.2f})")
    
    # ------------------------------------------------------------------
    # Configuración interactiva avanzada (filtros, dominios, resultados)
    # ------------------------------------------------------------------
    def configure_advanced_settings(self):
        """
        Menú interactivo para ajustar:
          - cantidad de resultados por consulta
          - dominios objetivo (target_sites)
          - dominios bloqueados / permitidos
          - extensiones de archivo
          - umbrales de riesgo / calidad
          - análisis profundo de URLs
        """
        while True:
            gf = getattr(self, "global_filters", {}) or {}
            print("\n⚙️  Configuración avanzada de Credential Finder")
            print("=" * 70)
            print(f"1. Resultados por consulta           : {self.default_num_results}")
            print(f"2. Dominios objetivo (target_sites)  : {', '.join(self.target_sites) if self.target_sites else 'TODOS'}")
            print(f"3. Dominios permitidos (post-filtro) : {', '.join(gf.get('allowed_domains') or []) or 'sin restricción'}")
            print(f"4. Dominios bloqueados (post-filtro) : {', '.join(gf.get('blocked_domains') or []) or 'ninguno'}")
            print(f"5. Extensiones requeridas (URL)      : {', '.join(gf.get('required_filetypes') or []) or 'ninguna'}")
            print(f"6. Umbral mínimo de riesgo           : {gf.get('min_risk_score') if gf.get('min_risk_score') is not None else 'sin mínimo'}")
            print(f"7. Umbral mínimo de calidad          : {gf.get('min_quality_score') if gf.get('min_quality_score') is not None else 'sin mínimo'}")
            print(f"8. Análisis profundo de URLs         : {'activado' if gf.get('analyze_urls', True) else 'desactivado'}")
            print(f"9. Filtros avanzados                 : {'activados' if getattr(self, 'use_advanced_filters', True) else 'desactivados'}")
            print("10. Resetear configuración a valores por defecto")
            print("11. Volver al menú principal")
            
            choice = input("\nSelecciona opción (1-11): ").strip()
            
            if choice == '1':
                value = input("Nuevo número de resultados por consulta (ej. 5, 10, 20): ").strip()
                try:
                    num = int(value)
                    if num > 0:
                        self.default_num_results = num
                        print(f"✅ default_num_results = {num}")
                except ValueError:
                    print("❌ Valor inválido.")
            
            elif choice == '2':
                value = input("Dominios objetivo separados por coma (ej: github.com,gitlab.com,pastebin.com) o vacío para solo github.com: ").strip()
                if value:
                    sites = [s.strip() for s in value.split(',') if s.strip()]
                    if sites:
                        self.target_sites = sites
                        print(f"✅ target_sites = {', '.join(self.target_sites)}")
                else:
                    self.target_sites = ["github.com"]
                    print("✅ target_sites reseteado a: github.com")
            
            elif choice == '3':
                value = input("Dominios PERMITIDOS separados por coma (vacío = sin restricción adicional): ").strip()
                if value:
                    gf["allowed_domains"] = [d.strip() for d in value.split(',') if d.strip()]
                else:
                    gf["allowed_domains"] = []
                self.global_filters = gf
                print("✅ Dominios permitidos actualizados.")
            
            elif choice == '4':
                value = input("Dominios BLOQUEADOS separados por coma (vacío = ninguno): ").strip()
                if value:
                    gf["blocked_domains"] = [d.strip() for d in value.split(',') if d.strip()]
                else:
                    gf["blocked_domains"] = []
                self.global_filters = gf
                print("✅ Dominios bloqueados actualizados.")
            
            elif choice == '5':
                value = input("Extensiones requeridas (sin punto, ej: env,yml,json) o vacío para ninguna: ").strip()
                if value:
                    gf["required_filetypes"] = [e.strip().lower() for e in value.split(',') if e.strip()]
                else:
                    gf["required_filetypes"] = []
                self.global_filters = gf
                print("✅ Extensiones requeridas actualizadas.")
            
            elif choice == '6':
                value = input("Umbral mínimo de riesgo (0.0 - 1.0, vacío = sin mínimo): ").strip()
                if value:
                    try:
                        v = float(value)
                        gf["min_risk_score"] = max(0.0, min(1.0, v))
                    except ValueError:
                        print("❌ Valor inválido, se mantiene el anterior.")
                else:
                    gf["min_risk_score"] = None
                self.global_filters = gf
                print("✅ Umbral de riesgo actualizado.")
            
            elif choice == '7':
                value = input("Umbral mínimo de calidad (0.0 - 1.0, vacío = sin mínimo): ").strip()
                if value:
                    try:
                        v = float(value)
                        gf["min_quality_score"] = max(0.0, min(1.0, v))
                    except ValueError:
                        print("❌ Valor inválido, se mantiene el anterior.")
                else:
                    gf["min_quality_score"] = None
                self.global_filters = gf
                print("✅ Umbral de calidad actualizado.")
            
            elif choice == '8':
                current = gf.get("analyze_urls", True)
                gf["analyze_urls"] = not current
                self.global_filters = gf
                print(f"✅ Análisis profundo de URLs ahora está {'activado' if gf['analyze_urls'] else 'desactivado'}.")
            
            elif choice == '9':
                self.use_advanced_filters = not getattr(self, "use_advanced_filters", True)
                print(f"✅ Filtros avanzados {'activados' if self.use_advanced_filters else 'desactivados'}.")
            
            elif choice == '10':
                # Restaurar configuración por defecto "razonable"
                self.default_num_results = int(os.getenv("CRED_FINDER_RESULTS_PER_QUERY", "5"))
                self.target_sites = [
                    "github.com",
                    "gitlab.com",
                    "bitbucket.org",
                    "gist.github.com",
                ]
                self.global_filters = {
                    "allowed_domains": [],
                    "blocked_domains": [
                        "stackoverflow.com",
                        "stackexchange.com",
                        "superuser.com",
                        "serverfault.com",
                        "quora.com",
                        "docs.github.com",
                        "github.community",
                    ],
                    "required_filetypes": [],
                    "min_quality_score": None,
                    "min_risk_score": None,
                    "analyze_urls": True,
                }
                self.use_advanced_filters = True
                print("✅ Configuración avanzada reseteada a valores por defecto.")
            
            elif choice == '11':
                break
            else:
                print("❌ Opción inválida.")

def main():
    finder = CredentialFinder()
    
    print("🚀 Buscador Avanzado de Credenciales - Enhanced with Cross-Engine Search")
    print("=" * 80)
    
    # Show engine info
    engine_info = finder.get_search_engine_info()
    print(f"🔍 Available Engines: {', '.join(engine_info['available_engines'])}")
    print(f"✅ Current Engine: {engine_info['engine_type']}")
    
    while True:
        print("\n" + "="*80)
        print("🔍 MENÚ PRINCIPAL - CREDENTIAL FINDER")
        print("="*80)
        print("1. Buscar archivos .env")
        print("2. Buscar archivos de configuración")
        print("3. Buscar credenciales")
        print("4. Buscar endpoints de API")
        print("5. Búsqueda Dork personalizada")
        print("6. Búsqueda multi-motor (.env)")
        print("7. Búsqueda multi-motor (todas las categorías)")
        print("8. Buscar API Keys - OpenAI")
        print("9. Buscar API Keys - GitHub Tokens")
        print("10. Buscar API Keys - Slack")
        print("11. Buscar API Keys - Google")
        print("12. Buscar API Keys - Square")
        print("13. Buscar API Keys - Shopify")
        print("14. Buscar API Keys - Todas las plataformas")
        print("15. Búsqueda multi-motor - API Keys")
        print("16. Comparar motores de búsqueda")
        print("17. Configurar motor de búsqueda")
        print("18. Mostrar estado de motores")
        print("19. Buscar en todas las categorías")
        print("20. Salir")
        print("21. Configuración avanzada (filtros, dominios, resultados)")
        
        choice = input("\nIngresa tu opción (1-21): ").strip()
        
        if choice == '1':
            results = finder.find_env_files()
            finder.display_results(results, "Archivos .env")
            if results:
                save = input("\n¿Guardar resultados? (s/n): ").lower()
                if save == 's':
                    finder.save_results(results, 'env_files_results.json')
                    
        elif choice == '2':
            results = finder.find_config_files()
            finder.display_results(results, "Archivos de configuración")
            if results:
                save = input("\n¿Guardar resultados? (s/n): ").lower()
                if save == 's':
                    finder.save_results(results, 'config_files_results.json')
                    
        elif choice == '3':
            results = finder.find_credentials()
            finder.display_results(results, "Credenciales")
            if results:
                save = input("\n¿Guardar resultados? (s/n): ").lower()
                if save == 's':
                    finder.save_results(results, 'credentials_results.json')
                    
        elif choice == '4':
            results = finder.find_api_endpoints()
            finder.display_results(results, "Endpoints de API")
            if results:
                save = input("\n¿Guardar resultados? (s/n): ").lower()
                if save == 's':
                    finder.save_results(results, 'api_endpoints_results.json')
                    
        elif choice == '5':
            custom_query = input("Ingresa tu consulta Dork personalizada: ")
            cross_engine = input("¿Usar búsqueda multi-motor? (s/n): ").lower() == 's'
            results = finder.dork_search(custom_query, use_cross_engine=cross_engine)
            
            if cross_engine:
                finder.display_results(results, f"Dork personalizada (Cross-Engine)", is_cross_engine=True)
            else:
                finder.display_results(results, "Búsqueda Dork personalizada")
            
            if results:
                save = input("\n¿Guardar resultados? (s/n): ").lower()
                if save == 's':
                    filename = 'custom_dork_cross_engine_results.json' if cross_engine else 'custom_dork_results.json'
                    finder.save_results(results, filename)
                    
        elif choice == '6':
            print("\n🔍 Búsqueda Multi-Motor para Archivos .env")
            results = finder.find_env_files_cross_engine()
            finder.display_results(results, "Archivos .env (Cross-Engine)", is_cross_engine=True)
            finder.display_engine_comparison(results)
            
            if results:
                save = input("\n¿Guardar resultados? (s/n): ").lower()
                if save == 's':
                    finder.save_results(results, 'env_files_cross_engine_results.json')
                    
        elif choice == '7':
            print("\n🔍 Búsqueda Multi-Motor para Todas las Categorías")
            all_results = {}
            
            categories = [
                ('env_files', finder.find_env_files_cross_engine),
                ('config_files', lambda: finder.cross_engine_search('site:github.com config "password"')),
                ('credentials', lambda: finder.cross_engine_search('site:github.com "password" "api_key"')),
                ('api_endpoints', lambda: finder.cross_engine_search('site:github.com "api" "endpoint"'))
            ]
            
            for category_name, search_func in categories:
                print(f"\n🔍 Searching {category_name.replace('_', ' ').title()} with multiple engines...")
                try:
                    results = search_func()
                    all_results[category_name] = results
                    finder.display_results(results, category_name.replace('_', ' ').title(), is_cross_engine=True)
                    time.sleep(2)  # Rate limiting
                except Exception as e:
                    print(f"❌ Error in {category_name}: {e}")
                    all_results[category_name] = {}
            
            # Save all results
            finder.save_results(all_results, 'all_cross_engine_results.json')
            print(f"\n📊 Cross-Engine Summary:")
            for category, results in all_results.items():
                if isinstance(results, dict) and 'total_unique_urls' in results:
                    print(f"  {category.replace('_', ' ').title()}: {results['total_unique_urls']} unique URLs")
                    
        # API Key Search Options
        elif choice == '8':
            results = finder.find_openai_api_keys()
            finder.display_results(results, "OpenAI API Keys")
            if results:
                save = input("\n¿Guardar resultados? (s/n): ").lower()
                if save == 's':
                    finder.save_results(results, 'openai_api_keys_results.json')
        
        elif choice == '9':
            results = finder.find_github_tokens()
            finder.display_results(results, "GitHub Tokens")
            if results:
                save = input("\n¿Guardar resultados? (s/n): ").lower()
                if save == 's':
                    finder.save_results(results, 'github_tokens_results.json')
        
        elif choice == '10':
            results = finder.find_slack_tokens()
            finder.display_results(results, "Slack Tokens")
            if results:
                save = input("\n¿Guardar resultados? (s/n): ").lower()
                if save == 's':
                    finder.save_results(results, 'slack_tokens_results.json')
        
        elif choice == '11':
            results = finder.find_google_api_keys()
            finder.display_results(results, "Google API Keys")
            if results:
                save = input("\n¿Guardar resultados? (s/n): ").lower()
                if save == 's':
                    finder.save_results(results, 'google_api_keys_results.json')
        
        elif choice == '12':
            results = finder.find_square_tokens()
            finder.display_results(results, "Square Tokens")
            if results:
                save = input("\n¿Guardar resultados? (s/n): ").lower()
                if save == 's':
                    finder.save_results(results, 'square_tokens_results.json')
        
        elif choice == '13':
            results = finder.find_shopify_secrets()
            finder.display_results(results, "Shopify Secrets")
            if results:
                save = input("\n¿Guardar resultados? (s/n): ").lower()
                if save == 's':
                    finder.save_results(results, 'shopify_secrets_results.json')
        
        elif choice == '14':
            print("\n🔍 Búsqueda de API Keys en Todas las Plataformas")
            results = finder.find_all_api_keys()
            
            # Display results for each platform
            for platform, platform_results in results.items():
                print(f"\n{'='*60}")
                print(f"🔑 Resultados para {platform.upper()}: {len(platform_results)} encontrados")
                print('='*60)
                
                # Show summary
                if platform_results:
                    print(f"📊 Mostrando resultados para {platform.upper()}")
                    finder.display_results(platform_results, f"API Keys - {platform.title()}")
                else:
                    print(f"❌ No se encontraron resultados para {platform.upper()}")
            
            # Save all results
            save = input("\n¿Guardar resultados de todas las plataformas? (s/n): ").lower()
            if save == 's':
                finder.save_results(results, 'all_api_keys_results.json')
        
        elif choice == '15':
            print("\n🔍 Búsqueda Multi-Motor de API Keys en Todas las Plataformas")
            results = finder.find_all_api_keys_cross_engine()
            
            # Display cross-engine results for each platform
            for platform, platform_results in results.items():
                print(f"\n{'='*60}")
                print(f"🔍 Resultados multi-motor para {platform.upper()}")
                print('='*60)
                
                if isinstance(platform_results, dict) and platform_results.get('total_unique_urls', 0) > 0:
                    finder.display_results(platform_results, f"API Keys {platform.title()} (Cross-Engine)", is_cross_engine=True)
                else:
                    print(f"❌ No se encontraron resultados para {platform.upper()}")
            
            # Save all results
            save = input("\n¿Guardar resultados multi-motor de todas las plataformas? (s/n): ").lower()
            if save == 's':
                finder.save_results(results, 'all_api_keys_cross_engine_results.json')
                    
        elif choice == '16':
            print("\n🔍 Comparación de Motores de Búsqueda")
            test_query = input("Ingresa query para comparar motores: ")
            if test_query:
                comparison = finder.cross_engine_search(test_query, num=10)
                finder.display_engine_comparison(comparison)
                
                save = input("\n¿Guardar comparación? (s/n): ").lower()
                if save == 's':
                    finder.save_results(comparison, f'engine_comparison_{test_query[:20]}.json')
                    
        elif choice == '17':
            print("\n⚙️ Configuración de Motor de Búsqueda")
            engine_info = finder.get_search_engine_info()
            print(f"Available engines: {', '.join(engine_info['available_engines'])}")
            
            while True:
                print("\nSelect engine:")
                print("1. Google")
                print("2. DuckDuckGo") 
                print("3. Auto-select best")
                print("4. Back to main menu")
                
                engine_choice = input("Choice (1-4): ").strip()
                
                if engine_choice == '1':
                    finder.set_search_engine(SearchEngineType.GOOGLE)
                    print("✅ Google engine selected")
                    break
                elif engine_choice == '2':
                    finder.set_search_engine(SearchEngineType.DUCKDUCKGO)
                    print("✅ DuckDuckGo engine selected")
                    break
                elif engine_choice == '3':
                    finder.set_search_engine(None)  # Auto-select
                    print("✅ Auto-select enabled")
                    break
                elif engine_choice == '4':
                    break
                else:
                    print("❌ Invalid choice")
                    
        elif choice == '18':
            print("\n🔍 Estado de Motores de Búsqueda")
            finder.search_manager.display_engine_status()
            engine_info = finder.get_search_engine_info()
            print(f"\n🔧 Configuration Status:")
            print(f"Google API: {'✅' if engine_info['google_api_available'] else '❌'}")
            print(f"SerpAPI: {'✅' if engine_info['serp_api_available'] else '❌'}")
            
        elif choice == '19':
            print("\n🔍 Búsqueda Completa (Single Engine)")
            all_results = {}
            categories = [
                ('env_files', finder.find_env_files),
                ('config_files', finder.find_config_files),
                ('credentials', finder.find_credentials),
                ('api_endpoints', finder.find_api_endpoints),
                ('openai_keys', finder.find_openai_api_keys),
                ('github_tokens', finder.find_github_tokens),
                ('slack_tokens', finder.find_slack_tokens),
                ('google_keys', finder.find_google_api_keys),
                ('square_tokens', finder.find_square_tokens),
                ('shopify_secrets', finder.find_shopify_secrets)
            ]
            
            for category_name, search_func in categories:
                print(f"\n🔍 Buscando {category_name.replace('_', ' ').title()}...")
                try:
                    results = search_func()
                    all_results[category_name] = results
                    finder.display_results(results, category_name.replace('_', ' ').title())
                    time.sleep(2)  # Rate limiting
                except Exception as e:
                    print(f"❌ Error in {category_name}: {e}")
                    all_results[category_name] = []
            
            # Save all results
            finder.save_results(all_results, 'all_results_complete.json')
            print(f"\n📊 Resumen de resultados totales:")
            for category, results in all_results.items():
                print(f"  {category.replace('_', ' ').title()}: {len(results)} encontrados")
                
        elif choice == '20':
            print("👋 ¡Gracias por usar el Buscador Avanzado de Credenciales!")
            print("🔒 Recuerda: utiliza esta herramienta de forma responsable y ética.")
            break
            
        elif choice == '21':
            finder.configure_advanced_settings()
            
        else:
            print("❌ Opción inválida. Inténtalo de nuevo.")
            
        # Brief pause between operations
        time.sleep(1)

if __name__ == "__main__":
    main()