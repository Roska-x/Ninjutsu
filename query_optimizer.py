#!/usr/bin/env python3
"""
Query Optimizer for Search Engines
Handles engine-specific search operator differences and optimization
"""

import re
from typing import Dict, List, Optional, Tuple
from search_engine_interface import SearchEngineType


class QueryOptimizer:
    """
    Optimizes search queries for different search engines
    Handles operator differences and engine-specific optimizations
    """
    
    # Google operators that DuckDuckGo doesn't support or supports differently
    GOOGLE_ONLY_OPERATORS = [
        'inanchor:', 'allinanchor:', 'inurl:', 'allinurl:', 
        'intitle:', 'allintitle:', 'intext:', 'allintext:',
        'filetype:', 'site:', 'link:', 'related:', 'cache:'
    ]
    
    # DuckDuckGo-friendly replacements for Google operators
    DDG_OPERATOR_MAP = {
        'filetype:': 'type:',  # Partial support
        'site:': 'site:',      # DuckDuckGo supports this
        'inurl:': '',          # Remove unsupported operators
        'intitle:': '',        # Remove unsupported operators
        'intext:': '',         # Remove unsupported operators
        'allinurl:': '',       # Remove unsupported operators
        'allintitle:': '',     # Remove unsupported operators
        'allintext:': '',      # Remove unsupported operators
        'inanchor:': '',       # Remove unsupported operators
        'allinanchor:': '',    # Remove unsupported operators
        'link:': '',           # Remove unsupported operators
        'related:': '',        # Remove unsupported operators
        'cache:': ''           # Remove unsupported operators
    }
    
    # Google-specific dork patterns that work well
    GOOGLE_OPTIMAL_PATTERNS = {
        'env_files': [
            'site:github.com "filetype:env" OR "password" OR "database"',
            'site:github.com ".env" "DB_PASSWORD"',
            'site:github.com "API_KEY" filetype:env'
        ],
        'config_files': [
            'site:github.com "config.json" "password"',
            'site:github.com "settings.js" "secret"',
            'site:github.com "config.php" "db_password"'
        ],
        'credentials': [
            'site:github.com "password" "admin"',
            'site:github.com "AWS_ACCESS_KEY_ID"',
            'site:github.com "private_key" "-----BEGIN"'
        ],
        'api_endpoints': [
            'site:github.com "api/v1" "endpoint"',
            'site:github.com "swagger" "api"',
            'site:github.com "graphql" "endpoint"'
        ]
    }
    
    # DuckDuckGo optimized patterns
    DDG_OPTIMAL_PATTERNS = {
        'env_files': [
            'site:github.com .env password OR database OR api_key',
            'site:github.com ".env" "password" OR "database"',
            'site:github.com environment OR config "password"'
        ],
        'config_files': [
            'site:github.com config "password" OR "secret" OR "api_key"',
            'site:github.com settings OR configuration "database"',
            'site:github.com ".env" OR ".config" "password"'
        ],
        'credentials': [
            'site:github.com "password" "admin" OR "root"',
            'site:github.com "AWS_ACCESS_KEY_ID" OR "api_key"',
            'site:github.com "-----BEGIN" private OR key'
        ],
        'api_endpoints': [
            'site:github.com api "endpoint" OR "swagger"',
            'site:github.com "REST API" OR "graphql" "documentation"',
            'site:github.com "postman" "collection" OR "api_docs"'
        ]
    }
    
    @classmethod
    def optimize_query(cls, query: str, engine_type: SearchEngineType) -> str:
        """
        Optimize a search query for a specific search engine.
        
        Args:
            query: Original search query
            engine_type: Target search engine type
        
        Returns:
            Optimized query string
        """
        # Serper-backed Google search uses essentially the same operators as Google,
        # so we reuse the same optimization path.
        if engine_type in (SearchEngineType.GOOGLE, SearchEngineType.SERPER_GOOGLE):
            return cls._optimize_for_google(query)
        elif engine_type == SearchEngineType.DUCKDUCKGO:
            return cls._optimize_for_duckduckgo(query)
        else:
            return query
    
    @classmethod
    def _optimize_for_google(cls, query: str) -> str:
        """
        Optimize query for Google (keep most operators, enhance structure)
        """
        # Google supports most operators, so we mainly clean up and optimize structure
        optimized = query.strip()
        
        # Ensure proper spacing around operators
        for operator in cls.GOOGLE_ONLY_OPERATORS:
            # Add space after operator if missing
            optimized = re.sub(f'{re.escape(operator)}(?!\\s)', f'{operator} ', optimized)
        
        return optimized
    
    @classmethod
    def _optimize_for_duckduckgo(cls, query: str) -> str:
        """
        Optimize query for DuckDuckGo (replace/remove unsupported operators)
        """
        optimized = query.strip()
        
        # Replace Google-specific operators with DuckDuckGo-friendly ones
        for google_op, ddg_op in cls.DDG_OPERATOR_MAP.items():
            optimized = optimized.replace(google_op, ddg_op)
        
        # Clean up excessive spacing and operators
        optimized = re.sub(r'\s+', ' ', optimized)  # Multiple spaces to single
        optimized = re.sub(r'\s+OR\s+', ' OR ', optimized)  # Clean OR spacing
        optimized = re.sub(r'\s+AND\s+', ' AND ', optimized)  # Clean AND spacing
        
        # Remove empty quotes and other artifacts
        optimized = re.sub(r'""', '', optimized)
        optimized = re.sub(r'""', '', optimized)
        
        return optimized.strip()
    
    @classmethod
    def get_optimal_queries(cls, category: str, engine_type: SearchEngineType) -> List[str]:
        """
        Get engine-specific optimized queries for a category.
        
        Args:
            category: Query category (env_files, config_files, etc.)
            engine_type: Target search engine
        
        Returns:
            List of optimized queries
        """
        if engine_type in (SearchEngineType.GOOGLE, SearchEngineType.SERPER_GOOGLE):
            return cls.GOOGLE_OPTIMAL_PATTERNS.get(category, [])
        elif engine_type == SearchEngineType.DUCKDUCKGO:
            return cls.DDG_OPTIMAL_PATTERNS.get(category, [])
        else:
            return []
    
    @classmethod
    def analyze_query_compatibility(cls, query: str) -> Dict[str, bool]:
        """
        Analyze query compatibility with different engines
        
        Args:
            query: Query to analyze
        
        Returns:
            Dictionary with compatibility scores for each engine
        """
        google_compatible = True
        ddg_compatible = True
        
        # Check for Google-specific operators
        google_operators_found = []
        for op in cls.GOOGLE_ONLY_OPERATORS:
            if op in query:
                google_operators_found.append(op)
        
        # DuckDuckGo compatibility check
        for google_op, ddg_op in cls.DDG_OPERATOR_MAP.items():
            if google_op in query and ddg_op == '':
                ddg_compatible = False
                break
        
        return {
            'google': google_compatible,
            'duckduckgo': ddg_compatible,
            'google_operators_found': google_operators_found,
            'recommendation': cls._get_recommendation(google_compatible, ddg_compatible)
        }
    
    @classmethod
    def _get_recommendation(cls, google_compatible: bool, ddg_compatible: bool) -> str:
        """Get optimization recommendation based on compatibility"""
        if google_compatible and ddg_compatible:
            return "Query works well with both engines"
        elif google_compatible and not ddg_compatible:
            return "Use Google for best results"
        elif not google_compatible and ddg_compatible:
            return "Use DuckDuckGo for best results"
        else:
            return "Query needs manual optimization"
    
    @classmethod
    def suggest_improvements(cls, query: str, engine_type: SearchEngineType) -> List[str]:
        """
        Suggest improvements for a query based on engine characteristics.
        
        Args:
            query: Query to analyze
            engine_type: Target engine
        
        Returns:
            List of improvement suggestions
        """
        suggestions: List[str] = []
        
        if engine_type == SearchEngineType.DUCKDUCKGO:
            # Check for unsupported operators
            for google_op in cls.GOOGLE_ONLY_OPERATORS:
                if google_op in query:
                    suggestions.append(f"Consider removing '{google_op}' operator for DuckDuckGo")
            
            # Suggest adding more general terms
            if 'filetype:' in query:
                suggestions.append("Replace 'filetype:' with broader terms for DuckDuckGo")
            
            # Suggest DuckDuckGo-specific optimizations
            if 'site:' not in query:
                suggestions.append("Consider adding 'site:github.com' to focus results")
        
        elif engine_type in (SearchEngineType.GOOGLE, SearchEngineType.SERPER_GOOGLE):
            # Suggest Google / Serper-specific optimizations
            if 'site:' not in query:
                suggestions.append("Consider adding 'site:github.com' for better targeting")
            
            if 'filetype:' not in query and any(term in query.lower() for term in ['config', 'env', 'password']):
                suggestions.append("Consider using 'filetype:' operator for specific file types")
        
        return suggestions
    
    @classmethod
    def get_engine_specific_tips(cls, engine_type: SearchEngineType) -> List[str]:
        """
        Get general tips for using a specific search engine.
        
        Args:
            engine_type: Search engine type
        
        Returns:
            List of usage tips
        """
        if engine_type in (SearchEngineType.GOOGLE, SearchEngineType.SERPER_GOOGLE):
            return [
                "Use 'filetype:' for specific file types (pdf, txt, env, etc.)",
                "Use 'site:' to restrict searches to specific domains",
                "Use 'intitle:' and 'inurl:' for more targeted results",
                "Combine operators with AND, OR, and parentheses for complex queries",
                "Use quotation marks for exact phrase matching",
            ]
        elif engine_type == SearchEngineType.DUCKDUCKGO:
            return [
                "Use 'site:' to restrict searches to specific domains",
                "Use quotation marks for exact phrase matching",
                "Combine terms with OR for broader results",
                "Avoid complex operator combinations",
                "Use simple, descriptive terms for better results",
            ]
        else:
            return []


class EngineAwareSearchManager:
    """
    Wrapper around UnifiedSearchManager that applies query optimization
    """
    
    def __init__(self, search_manager, auto_optimize: bool = True):
        self.search_manager = search_manager
        self.auto_optimize = auto_optimize
        self.optimizer = QueryOptimizer()
    
    def search(self, query: str, num: int = 10, **kwargs):
        """
        Perform search with automatic query optimization
        """
        current_engine = self.search_manager.get_current_engine()
        
        if self.auto_optimize and current_engine:
            # Analyze query compatibility
            compatibility = self.optimizer.analyze_query_compatibility(query)
            
            # Show recommendations if needed
            if compatibility['recommendation'] != "Query works well with both engines":
                print(f"💡 Query optimization: {compatibility['recommendation']}")
            
            # Optimize query for current engine
            optimized_query = self.optimizer.optimize_query(query, current_engine)
            
            if optimized_query != query:
                print(f"🔧 Optimized query: {optimized_query}")
                query = optimized_query
        
        return self.search_manager.search(query, num, **kwargs)
    
    def cross_engine_search_with_optimization(self, query: str, num: int = 10):
        """
        Perform cross-engine search with per-engine query optimization
        """
        optimized_queries = {}
        
        for engine_type in self.search_manager.get_available_engines():
            optimized_query = self.optimizer.optimize_query(query, engine_type)
            optimized_queries[engine_type] = optimized_query
        
        print("🔧 Cross-engine query optimization:")
        for engine, optimized_query in optimized_queries.items():
            if optimized_query != query:
                print(f"  {engine.value}: {optimized_query}")
            else:
                print(f"  {engine.value}: {query} (no optimization needed)")
        
        # Perform search with optimized queries
        results = {}
        for engine_type in self.search_manager.get_available_engines():
            try:
                print(f"🔍 Searching with {engine_type.value}...")
                self.search_manager.set_engine(engine_type)
                query_to_use = optimized_queries[engine_type]
                engine_results = self.search_manager.search(query_to_use, num)
                results[engine_type] = engine_results
            except Exception as e:
                print(f"❌ Error with {engine_type.value}: {e}")
                results[engine_type] = []
        
        return results


# Convenience functions
def optimize_query_for_engine(query: str, engine_type: SearchEngineType) -> str:
    """Convenience function to optimize a query for a specific engine"""
    return QueryOptimizer.optimize_query(query, engine_type)


def get_engine_tips(engine_type: SearchEngineType) -> List[str]:
    """Convenience function to get engine-specific tips"""
    return QueryOptimizer.get_engine_specific_tips(engine_type)


if __name__ == "__main__":
    # Test the query optimizer
    print("🔧 Query Optimizer Test")
    print("=" * 50)
    
    test_queries = [
        'site:github.com filetype:env "password"',
        'site:github.com "config.json" "api_key"',
        'site:github.com intitle:index.of "admin"',
        'site:github.com inurl:config "database"'
    ]
    
    for query in test_queries:
        print(f"\nOriginal query: {query}")
        
        # Analyze compatibility
        compatibility = QueryOptimizer.analyze_query_compatibility(query)
        print(f"  Google compatible: {compatibility['google']}")
        print(f"  DuckDuckGo compatible: {compatibility['duckduckgo']}")
        print(f"  Recommendation: {compatibility['recommendation']}")
        
        # Show optimizations
        google_optimized = QueryOptimizer.optimize_query(query, SearchEngineType.GOOGLE)
        ddg_optimized = QueryOptimizer.optimize_query(query, SearchEngineType.DUCKDUCKGO)
        
        print(f"  Google optimized: {google_optimized}")
        print(f"  DuckDuckGo optimized: {ddg_optimized}")