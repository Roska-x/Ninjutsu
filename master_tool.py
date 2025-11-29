#!/usr/bin/env python3
"""
Master Credential Discovery Tool - Enhanced with Multi-Engine Support
Unified interface for all credential finding and security assessment tools
Supports both Google Custom Search and DuckDuckGo via SerAPI
"""

import os
import sys
import time
import json
from datetime import datetime
from typing import Optional

# Import all our tools
try:
    from credential_finder import CredentialFinder
    from subdomain_finder import SubdomainFinder
    from report_generator import ReportGenerator
    from google_dorking_templates import GoogleDorkTemplates
    from dork_engine import DorkEngine
    from search_engine_interface import SearchEngineType
    from query_optimizer import QueryOptimizer, EngineAwareSearchManager
    from interactive_dork_interface import InteractiveDorkInterface
    from llm_dork_assistant import GroqDorkAssistant
    from smart_search import SmartSearch
except ImportError as e:
    print(f"❌ Error importing modules: {e}")
    print("Make sure all required modules are installed:")
    print("pip install requests dnspython python-dotenv")
    sys.exit(1)

class MasterSecurityTool:
    def __init__(self, engine_type: SearchEngineType = None):
        """
        Initialize MasterSecurityTool with multi-engine support
        
        Args:
            engine_type: Preferred search engine (Google or DuckDuckGo)
        """
        self.credential_finder = CredentialFinder(engine_type)
        self.subdomain_finder = SubdomainFinder()
        self.report_generator = ReportGenerator()
        self.dork_engine = DorkEngine(engine_type)
        self.interactive_dork_interface = InteractiveDorkInterface(self.dork_engine)
        self.llm_dork_assistant = None  # Se inicializa bajo demanda
        
        # Track the preferred engine
        self.preferred_engine = engine_type
        self.global_engine_selection = engine_type
        
        # Initialize query optimizer if available
        try:
            self.query_optimizer = QueryOptimizer()
        except ImportError:
            self.query_optimizer = None
    
    def set_global_search_engine(self, engine_type: Optional[SearchEngineType]):
        """
        Set the global search engine preference and propagate to all tools.
        
        Args:
            engine_type: Search engine to set as global preference, or None to enable auto-select.
        """
        try:
            # Update preferred engine (may be None for auto-select)
            self.preferred_engine = engine_type
            self.global_engine_selection = engine_type
            
            if engine_type is None:
                # Enable auto-select in underlying tools
                self.credential_finder.set_search_engine(None)
                # Use DorkEngine's auto-selection helper to avoid passing None into set_engine()
                self.dork_engine.auto_select_engine()
                print("✅ Global auto-select enabled for all tools")
            else:
                # Propagate explicit engine choice
                self.credential_finder.set_search_engine(engine_type)
                self.dork_engine.set_engine(engine_type)
                print(f"✅ Global engine set to: {engine_type.value.title()}")
            
        except Exception as e:
            print(f"❌ Error setting global engine: {e}")
    
    def get_global_engine_info(self) -> dict:
        """
        Get information about the global engine configuration
        
        Returns:
            Dictionary with global engine information
        """
        try:
            cred_info = self.credential_finder.get_search_engine_info()
            return {
                'global_preference': self.global_engine_selection.value if self.global_engine_selection else 'Auto-select',
                'credential_finder_engine': cred_info.get('engine_type'),
                'available_engines': cred_info.get('available_engines', []),
                'google_api_available': cred_info.get('google_api_available', False),
                'serp_api_available': cred_info.get('serp_api_available', False),
                'query_optimizer_available': self.query_optimizer is not None
            }
        except Exception as e:
            return {
                'global_preference': self.global_engine_selection.value if self.global_engine_selection else 'Unknown',
                'error': str(e)
            }
        
    def show_banner(self):
        """Mostrar banner principal de la herramienta"""
        banner = """
╔═══════════════════════════════════════════════════════════════════╗
║                                                                   ║
║   🔍 KIT AVANZADO DE DESCUBRIMIENTO DE CREDENCIALES 🔍            ║
║                               by Roska                            ║
║   • Google Dorking + DuckDuckGo para archivos sensibles           ║
║   • Búsqueda de credenciales multi-motor                          ║
║   • Descubrimiento de endpoints de API                            ║
║   • Enumeración de subdominios                                    ║
║   • Generación automática de reportes                             ║
║   • Evaluación y análisis de riesgo                               ║
║   • Comparación avanzada entre motores                            ║
║                                                                   ║
╚═══════════════════════════════════════════════════════════════════╝
        """
        print(banner)
     
    def show_menu(self):
        """Mostrar el menú principal"""
        menu = """
┌─────────────────────────────────────────────────────────────────┐
│                         MENÚ PRINCIPAL                          │
├─────────────────────────────────────────────────────────────────┤
│  1. 🔍 Buscador de credenciales (interactivo)                   │
│  2. 🌐 Descubrimiento de subdominios                            │
│  3. 📊 Plantillas de Google Dorking                             │
│  4. 🧨 Dorks avanzados multi-motor (Google + DuckDuckGo)        │
│  5. 📚 Búsqueda de libros PDF                                   │
│  6. 🔄 Búsqueda cruzada entre motores                           │
│  7. 📈 Generar reportes                                         │
│  8. 🚀 Escaneo rápido (todas las herramientas)                  │
│  9. ⚙️  Configuración motores                                    │
│ 10. 📊 Comparación de rendimiento                               │
│ 11. 📚 Ayuda y documentación                                    │
│ 12. 🖼️  Búsquedas avanzadas (imágenes / noticias / trending)     │
│ 13. 🧨 Dorks interactivos (selección personalizada)             │
│ 14. 📹 Modo cámaras (dorks personalizados)                      │
│ 15. 🔑 Búsqueda de API Keys (todas las plataformas)             │
│ 16. 🤖 Asistente LLM de dorks (Groq)                            │
│ 17. 🔎 SmartSearch sobre resultados locales                     │
│ 18. ❌ Salir                                                    │
└─────────────────────────────────────────────────────────────────┘
        """
        print(menu)
        
        # Show current engine status
        self._display_engine_status()
    
    def _display_engine_status(self):
        """Display current search engine status"""
        try:
            cred_info = self.credential_finder.get_search_engine_info()
            dork_info = self.dork_engine.get_engine_info()

            print(f"\n🔍 Estado de Motores:")
            print(f"   Actual: {cred_info['engine_type'].title() if cred_info['engine_type'] else 'Auto-select'}")
            print(f"   Google API: {'✅' if cred_info['google_api_available'] else '❌'}")
            print(f"   SerpAPI: {'✅' if cred_info['serp_api_available'] else '❌'}")
            print(f"   Serper (Google): {'✅' if cred_info.get('serper_api_available') else '❌'}")
            print(f"   Selenium (Google): {'✅' if cred_info.get('selenium_available') else '❌'}")
        except Exception:
            # If we can't get engine info, just continue
            pass
    
    def quick_scan(self, domain=None):
        """Realizar un escaneo rápido y completo usando todas las herramientas"""
        if not domain:
            domain = input("Ingresa el dominio objetivo para el escaneo rápido: ").strip()
        
        if not domain:
            print("❌ El dominio no puede estar vacío")
            return
        
        print(f"\n🚀 Starting Quick Security Scan for: {domain}")
        print("=" * 60)
        
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        scan_results = {
            'domain': domain,
            'timestamp': timestamp,
            'credential_finding': [],
            'subdomains': {},
            'scan_summary': {}
        }
        
        # 1. Subdomain Discovery
        print("\n🔍 Step 1: Discovering Subdomains...")
        try:
            subdomain_results = self.subdomain_finder.discover_subdomains(domain)
            scan_results['subdomains'] = subdomain_results
            
            if subdomain_results['subdomains']:
                print(f"  ✅ Found {len(subdomain_results['subdomains'])} subdomains")
                
                # Test each subdomain for credentials
                for subdomain in subdomain_results['subdomains']:
                    print(f"  🔍 Scanning subdomain: {subdomain}")
                    # You could add subdomain-specific credential scanning here
                    
        except Exception as e:
            print(f"  ❌ Error in subdomain discovery: {e}")
        
        # 2. Credential Discovery
        print("\n🔍 Step 2: Credential Discovery...")
        try:
            # Use predefined dorking queries
            env_results = self.credential_finder.find_env_files()
            config_results = self.credential_finder.find_config_files()
            cred_results = self.credential_finder.find_credentials()
            api_results = self.credential_finder.find_api_endpoints()
            
            scan_results['credential_finding'] = {
                'env_files': env_results,
                'config_files': config_results,
                'credentials': cred_results,
                'api_endpoints': api_results
            }
            
            total_creds = len(env_results) + len(config_results) + len(cred_results) + len(api_results)
            print(f"  ✅ Found {total_creds} credential-related results")
            
        except Exception as e:
            print(f"  ❌ Error in credential discovery: {e}")
        
        # 3. Generate Summary
        print("\n📊 Step 3: Generating Scan Summary...")
        total_subdomains = len(scan_results['subdomains'].get('subdomains', []))
        total_credentials = sum(len(v) for v in scan_results['credential_finding'].values() if isinstance(v, list))
        
        scan_results['scan_summary'] = {
            'total_subdomains': total_subdomains,
            'total_credential_findings': total_credentials,
            'scan_duration': 'N/A',  # Could be calculated
            'risk_level': self._assess_risk_level(total_credentials, total_subdomains)
        }
        
        # 4. Generate Report
        print("\n📈 Step 4: Generating Report...")
        try:
            report_files = self.report_generator.generate_comprehensive_report(
                scan_results, 
                f"Quick Security Scan - {domain}"
            )
            print(f"  ✅ Reports generated successfully!")
            print(f"     - HTML: {os.path.basename(report_files['html'])}")
            print(f"     - Text: {os.path.basename(report_files['text'])}")
            print(f"     - JSON: {os.path.basename(report_files['json'])}")
        except Exception as e:
            print(f"  ❌ Error generating report: {e}")
        
        # Display Summary
        self._display_scan_summary(scan_results)
        
        return scan_results
    
    def _assess_risk_level(self, credential_count, subdomain_count):
        """Assess overall risk level"""
        if credential_count > 20 or subdomain_count > 50:
            return "HIGH"
        elif credential_count > 10 or subdomain_count > 20:
            return "MEDIUM"
        elif credential_count > 0 or subdomain_count > 0:
            return "LOW"
        else:
            return "MINIMAL"
    
    def _display_scan_summary(self, results):
        """Display scan summary"""
        summary = results['scan_summary']
        
        print(f"\n" + "="*60)
        print(f"🎯 QUICK SCAN SUMMARY - {results['domain']}")
        print("="*60)
        print(f"📊 Total Subdomains Found: {summary['total_subdomains']}")
        print(f"🔑 Credential Findings: {summary['total_credential_findings']}")
        print(f"🚨 Risk Level: {summary['risk_level']}")
        print(f"⏰ Scan Time: {results['timestamp']}")
        print("="*60)
        
        if summary['risk_level'] in ['HIGH', 'MEDIUM']:
            print("\n⚠️  WARNING: Potential security issues detected!")
            print("📁 Check the generated reports for detailed findings.")
        elif summary['risk_level'] == 'LOW':
            print("\n✅ LOW RISK: Minor findings detected.")
        else:
            print("\n✅ MINIMAL RISK: No significant security issues found.")
    
    def _sanitize_filename(self, text, prefix="results"):
        """Create a filesystem-safe filename based on user input."""
        safe = "".join(c if c.isalnum() or c in ("-", "_") else "_" for c in text)
        safe = safe.strip("_")
        if not safe:
            safe = prefix
        return safe
    
    def _save_generic_results(self, results, default_filename):
        """Helper to save generic results to JSON using CredentialFinder."""
        if not results:
            print("❌ No results to save.")
            return
        
        # Aclarar al usuario que el programa está esperando entrada
        save = input("\n💾 Save results to JSON file? (y/n, Enter = n): ").strip().lower()
        if save == 'y':
            self.credential_finder.save_results(results, default_filename)
        else:
            print("ℹ️  Results were not saved. Returning to the main menu...")
    
    def credential_finder_menu(self):
        """Run credential finder tool"""
        print("\n🔍 Credential Finder - Interactive Mode")
        from credential_finder import main as credential_main
        credential_main()
    
    def subdomain_discovery_menu(self):
        """Ejecutar la herramienta de descubrimiento de subdominios"""
        print("\n🌐 Herramienta de descubrimiento de subdominios")
        domain = input("Ingresa el dominio: ").strip()
        if domain:
            results = self.subdomain_finder.discover_subdomains(domain)
            
            # Guardar resultados
            save = input("¿Guardar resultados en un archivo JSON? (y/n): ").lower()
            if save == 'y':
                filename = f"{domain.replace('.', '_')}_subdomains.json"
                self.subdomain_finder.save_results(results, filename)
    
    def dorking_templates_menu(self):
        """Display Google Dorking templates"""
        print("\n📚 Google Dorking Templates")
        print("=" * 50)
        
        templates = GoogleDorkTemplates.all_templates()
        
        for category, queries in templates.items():
            print(f"\n🔍 {category.replace('_', ' ').title()}:")
            print("-" * 40)
            for i, query in enumerate(queries, 1):
                print(f"{i:2d}. {query}")
    
    def advanced_dorks_menu(self):
        """Menú interactivo para ejecutar dorks avanzados desde el catálogo."""
        print("\n🧨 Dorks avanzados de Google (catálogo)")
        print("=" * 60)
        
        categories = self.dork_engine.catalog.get_categories()
        if not categories:
            print("❌ No se encontraron categorías de dorks en dorks_catalog.json")
            return
        
        while True:
            print("\nCategorías disponibles:")
            for idx, cat in enumerate(categories, 1):
                print(f"{idx:2d}. {cat.replace('_', ' ').title()}")
            print("  0. Volver al menú principal")
            
            choice = input("\nSelecciona una categoría (número): ").strip()
            if choice == '0':
                return
            
            try:
                idx = int(choice)
                if idx < 1 or idx > len(categories):
                    raise ValueError
            except ValueError:
                print("❌ Opción inválida. Por favor introduce un número válido.")
                continue
            
            category = categories[idx - 1]
            print(f"\n🔍 Ejecutando dorks para la categoría: {category.replace('_', ' ').title()}")
            try:
                results = self.dork_engine.run_category(category, verbose=True)
                combined = results.get("combined", [])
                
                if not combined:
                    print("\n❌ No se encontraron resultados para esta categoría.")
                else:
                    # Reuse CredentialFinder display for nice formatting and basic analysis.
                    self.credential_finder.display_results(combined, f"Dorks avanzados - {category.replace('_', ' ').title()}")
                    default_filename = f"advanced_{category}_results.json"
                    self._save_generic_results(combined, default_filename)
            except Exception as e:
                print(f"❌ Error al ejecutar los dorks avanzados: {e}")
            
            again = input("\n¿Ejecutar otra categoría? (y/n): ").lower()
            if again != 'y':
                break
    
    def advanced_dorks_multi_engine_menu(self):
        """Menú interactivo para ejecutar dorks avanzados en múltiples motores."""
        print("\n🧨 Dorks avanzados multi‑motor (catálogo)")
        print("=" * 60)
        
        categories = self.dork_engine.catalog.get_categories()
        if not categories:
            print("❌ No se encontraron categorías de dorks en dorks_catalog.json")
            return
        
        while True:
            print("\nCategorías disponibles:")
            for idx, cat in enumerate(categories, 1):
                print(f"{idx:2d}. {cat.replace('_', ' ').title()}")
            print("  0. Volver al menú principal")
            
            choice = input("\nSelecciona una categoría (número): ").strip()
            if choice == '0':
                return
            
            try:
                idx = int(choice)
                if idx < 1 or idx > len(categories):
                    raise ValueError
            except ValueError:
                print("❌ Opción inválida. Por favor introduce un número válido.")
                continue
            
            category = categories[idx - 1]
            print(f"\n🔍 Ejecutando dorks multi‑motor para la categoría: {category.replace('_', ' ').title()}")
            try:
                results = self.dork_engine.run_category_cross_engine(category, verbose=True)
                
                if not results.get('total_unique_urls', 0):
                    print("\n❌ No se encontraron resultados para esta categoría.")
                else:
                    # Display cross-engine results
                    self._display_cross_engine_results(results, f"Dorks avanzados - {category.replace('_', ' ').title()}")
                    
                    # Save results
                    default_filename = f"advanced_{category}_cross_engine_results.json"
                    self._save_generic_results(results, default_filename)
            except Exception as e:
                print(f"❌ Error al ejecutar dorks multi‑motor: {e}")
            
            again = input("\n¿Ejecutar otra categoría? (y/n): ").lower()
            if again != 'y':
                break
    
    def interactive_dorks_menu(self):
        """Interactive dork selection interface with pagination and customization"""
        print("\n🧨 Dorks Interactivos - Sistema Personalizado")
        print("=" * 60)
        print("Iniciando interfaz interactiva...")
        self.interactive_dork_interface.run_interactive_session()
    
    def cameras_mode_menu(self):
        """Modo especializado para búsquedas de cámaras (dorks personalizados/plantillas)."""
        print("\n📹 Modo avanzado de cámaras")
        print("=" * 60)
        
        camera_templates = [
            {
                "name": "Cámaras IP genéricas (view.shtml)",
                "query": 'intitle:"IP Camera" inurl:view.shtml',
            },
            {
                "name": "Paneles de login de cámaras genéricas",
                "query": 'intitle:"Camera Login" OR intitle:"Network Camera" "admin"',
            },
            {
                "name": "Cámaras Hikvision",
                "query": '"Hikvision" intitle:"Web Video Server" OR inurl:"/Streaming/channels/1"',
            },
            {
                "name": "Cámaras Dahua / DVR Web Client",
                "query": '"Dahua" "DVR Web Client"',
            },
            {
                "name": "Cámaras AXIS",
                "query": '"AXIS" intitle:"Network Camera" "Live View"',
            },
        ]
        
        while True:
            print("\nOpciones de cámaras:")
            print("1. Ejecutar dork personalizado (texto libre)")
            print("2. Usar plantillas de dorks de cámaras")
            print("3. Volver al menú principal")
            
            choice = input("\nSelecciona una opción (1-3): ").strip()
            
            if choice == '1':
                query = input("Ingresa el dork de cámaras (query completa): ").strip()
                if not query:
                    print("❌ La consulta no puede estar vacía.")
                    continue
                
                try:
                    # Búsqueda multi‑motor para este dork
                    comparison = self.dork_engine.search_manager.compare_results(query, num=10)
                    
                    adapted = {
                        "combined_by_engine": comparison.get("results_by_engine", {}),
                        "total_unique_urls": comparison.get("total_unique_urls", 0),
                        "overlap_percentage": comparison.get("overlap_percentage", {}),
                        "engines_tested": comparison.get("engines_tested", []),
                    }
                    
                    self._display_cross_engine_results(adapted, "Cámaras - dork personalizado")
                    
                    # Aplanar resultados para poder guardarlos
                    combined_results = []
                    for engine_results in adapted["combined_by_engine"].values():
                        combined_results.extend(engine_results)
                    
                    if combined_results:
                        # Deduplicar por enlace
                        seen = set()
                        deduped = []
                        for item in combined_results:
                            link = item.get("link")
                            if not link or link in seen:
                                continue
                            seen.add(link)
                            deduped.append(item)
                        
                        default_filename = "cameras_custom_dork_results.json"
                        self._save_generic_results(deduped, default_filename)
                    else:
                        print("❌ No se encontraron resultados para este dork.")
                except Exception as e:
                    print(f"❌ Error al ejecutar el dork personalizado de cámaras: {e}")
            
            elif choice == '2':
                print("\nPlantillas disponibles de cámaras:")
                for idx, tpl in enumerate(camera_templates, 1):
                    print(f"{idx:2d}. {tpl['name']}")
                print("  0. Volver")
                
                sel = input("\nSelecciona una plantilla: ").strip()
                if sel == '0':
                    continue
                
                try:
                    idx = int(sel)
                    if idx < 1 or idx > len(camera_templates):
                        raise ValueError
                except ValueError:
                    print("❌ Opción inválida.")
                    continue
                
                template = camera_templates[idx - 1]
                base_query = template["query"]
                
                extra = input("Filtro opcional (marca, país, ciudad, etc.) o Enter para omitir: ").strip()
                if extra:
                    query = f'{base_query} "{extra}"'
                else:
                    query = base_query
                
                print(f"\n🔍 Ejecutando dork de cámaras:\n   {query}")
                try:
                    comparison = self.dork_engine.search_manager.compare_results(query, num=10)
                    adapted = {
                        "combined_by_engine": comparison.get("results_by_engine", {}),
                        "total_unique_urls": comparison.get("total_unique_urls", 0),
                        "overlap_percentage": comparison.get("overlap_percentage", {}),
                        "engines_tested": comparison.get("engines_tested", []),
                    }
                    self._display_cross_engine_results(adapted, f"Cámaras - plantilla: {template['name']}")
                    
                    combined_results = []
                    for engine_results in adapted["combined_by_engine"].values():
                        combined_results.extend(engine_results)
                    
                    if combined_results:
                        seen = set()
                        deduped = []
                        for item in combined_results:
                            link = item.get("link")
                            if not link or link in seen:
                                continue
                            seen.add(link)
                            deduped.append(item)
                        
                        safe_name = self._sanitize_filename(template["name"], prefix="cameras_template")
                        default_filename = f"{safe_name}_results.json"
                        self._save_generic_results(deduped, default_filename)
                    else:
                        print("❌ No se encontraron resultados para esta plantilla.")
                except Exception as e:
                    print(f"❌ Error al ejecutar la plantilla de cámaras: {e}")
            
            elif choice == '3':
                return
            else:
                print("❌ Opción inválida. Por favor introduce un número entre 1 y 3.")
    
    def cross_engine_search_menu(self):
        """Menú para búsquedas de credenciales multi‑motor (cross‑engine)."""
        print("\n🔄 Búsqueda cruzada multi‑motor de credenciales")
        print("=" * 60)
        
        def _aplicar_filtros_avanzados(results_dict, titulo_base: str):
            """
            Aplicar filtros avanzados sobre los resultados combinados de una búsqueda multi‑motor.
            Usa CredentialFinder.filter_results_advanced() para afinar los hallazgos.
            """
            if not isinstance(results_dict, dict):
                print("❌ Resultados en formato inesperado, no se pueden filtrar.")
                return
            
            # Aplanar resultados por motor
            results_by_engine = results_dict.get("results_by_engine", {})
            combinados = []
            for engine_results in results_by_engine.values():
                if engine_results:
                    combinados.extend(engine_results)
            
            if not combinados:
                print("❌ No hay resultados combinados para aplicar filtros avanzados.")
                return
            
            usar_filtros = input("\n¿Aplicar filtros avanzados sobre los resultados combinados? (s/n): ").lower()
            if usar_filtros not in ("s", "y"):
                return
            
            # Palabras clave obligatorias
            kw = input("Palabras clave obligatorias (separadas por coma, opcional): ").strip()
            keywords = [k.strip() for k in kw.split(",") if k.strip()] if kw else None
            
            # Dominios permitidos / bloqueados
            allowed = input("Dominios PERMITIDOS (target.com,gov,edu, separados por coma, opcional): ").strip()
            allowed_domains = [d.strip() for d in allowed.split(",") if d.strip()] if allowed else None
            
            blocked = input("Dominios a EXCLUIR (github.com, gitlab.com, etc., separados por coma, opcional): ").strip()
            blocked_domains = [d.strip() for d in blocked.split(",") if d.strip()] if blocked else None
            
            # Extensiones requeridas
            ft = input("Extensiones requeridas (env,php,config,txt,log..., separadas por coma, opcional): ").strip()
            required_filetypes = [f.strip() for f in ft.split(",") if f.strip()] if ft else None
            
            # Scores mínimos
            def _leer_float(prompt: str):
                valor = input(prompt).strip()
                if not valor:
                    return None
                try:
                    return float(valor)
                except ValueError:
                    print("   ⚠️  Valor no válido, se ignora.")
                    return None
            
            min_quality = _leer_float("Mínimo quality_score (0.0–1.0, Enter para omitir): ")
            min_risk = _leer_float("Mínimo risk_score (0.0–1.0, Enter para omitir): ")
            
            filtrados = self.credential_finder.filter_results_advanced(
                combinados,
                keywords=keywords,
                allowed_domains=allowed_domains,
                blocked_domains=blocked_domains,
                required_filetypes=required_filetypes,
                min_quality_score=min_quality,
                min_risk_score=min_risk,
            )
            
            if not filtrados:
                print("❌ Ningún resultado cumple los filtros aplicados.")
                return
            
            print(f"\n📊 Resultados después de filtros avanzados: {len(filtrados)}")
            self.credential_finder.display_results(filtrados, f"{titulo_base} (filtrado)")
            
            guardar = input("\n¿Guardar resultados filtrados? (s/n): ").lower()
            if guardar in ("s", "y"):
                safe_title = self._sanitize_filename(titulo_base, prefix="cross_engine_filtered")
                self.credential_finder.save_results(filtrados, f"{safe_title}.json")
        
        while True:
            print("\nTipos de búsqueda disponibles:")
            print("1. .env multi‑motor")
            print("2. Archivos de configuración multi‑motor")
            print("3. Credenciales multi‑motor")
            print("4. Endpoints de API multi‑motor")
            print("5. Búsqueda personalizada multi‑motor")
            print("6. Volver al menú principal")
            
            choice = input("\nSelecciona tipo de búsqueda (1-6): ").strip()
            
            if choice == '1':
                print("\n🔍 Búsqueda multi‑motor de archivos .env")
                results = self.credential_finder.find_env_files_cross_engine()
                self.credential_finder.display_results(results, "Archivos .env (multi‑motor)", is_cross_engine=True)
                self.credential_finder.display_engine_comparison(results)
                
                _aplicar_filtros_avanzados(results, "Archivos .env (multi‑motor)")
                
                save = input("\n¿Guardar resultados brutos? (s/n): ").lower()
                if save in ('s', 'y'):
                    self.credential_finder.save_results(results, 'env_files_cross_engine_master.json')
            
            elif choice == '2':
                print("\n🔍 Búsqueda multi‑motor de archivos de configuración")
                query = 'site:github.com "config" "password"'
                results = self.credential_finder.cross_engine_search(query, num=10)
                self.credential_finder.display_results(results, "Archivos de configuración (multi‑motor)", is_cross_engine=True)
                self.credential_finder.display_engine_comparison(results)
                
                _aplicar_filtros_avanzados(results, "Archivos de configuración (multi‑motor)")
                
                save = input("\n¿Guardar resultados brutos? (s/n): ").lower()
                if save in ('s', 'y'):
                    self.credential_finder.save_results(results, 'config_files_cross_engine_master.json')
            
            elif choice == '3':
                print("\n🔍 Búsqueda multi‑motor de credenciales")
                query = 'site:github.com "password" "api_key"'
                results = self.credential_finder.cross_engine_search(query, num=10)
                self.credential_finder.display_results(results, "Credenciales (multi‑motor)", is_cross_engine=True)
                self.credential_finder.display_engine_comparison(results)
                
                _aplicar_filtros_avanzados(results, "Credenciales (multi‑motor)")
                
                save = input("\n¿Guardar resultados brutos? (s/n): ").lower()
                if save in ('s', 'y'):
                    self.credential_finder.save_results(results, 'credentials_cross_engine_master.json')
            
            elif choice == '4':
                print("\n🔍 Búsqueda multi‑motor de endpoints de API")
                query = 'site:github.com "api" "endpoint"'
                results = self.credential_finder.cross_engine_search(query, num=10)
                self.credential_finder.display_results(results, "Endpoints de API (multi‑motor)", is_cross_engine=True)
                self.credential_finder.display_engine_comparison(results)
                
                _aplicar_filtros_avanzados(results, "Endpoints de API (multi‑motor)")
                
                save = input("\n¿Guardar resultados brutos? (s/n): ").lower()
                if save in ('s', 'y'):
                    self.credential_finder.save_results(results, 'api_endpoints_cross_engine_master.json')
            
            elif choice == '5':
                custom_query = input("Ingresa la consulta personalizada para búsqueda multi‑motor: ").strip()
                if not custom_query:
                    print("❌ La consulta no puede estar vacía.")
                    continue
                
                results = self.credential_finder.cross_engine_search(custom_query, num=10)
                titulo = f"Dork personalizada (multi‑motor): {custom_query[:30]}"
                self.credential_finder.display_results(results, titulo, is_cross_engine=True)
                self.credential_finder.display_engine_comparison(results)
                
                _aplicar_filtros_avanzados(results, titulo)
                
                save = input("\n¿Guardar resultados brutos? (s/n): ").lower()
                if save in ('s', 'y'):
                    safe_query = self._sanitize_filename(custom_query, prefix="custom_query")
                    self.credential_finder.save_results(results, f'{safe_query}_cross_engine_master.json')
            
            elif choice == '6':
                # Volver al menú principal
                return
            
            else:
                print("❌ Opción inválida. Por favor selecciona un número entre 1 y 6.")
    
    def engine_performance_comparison_menu(self):
        """Menu for comparing performance between search engines"""
        print("\n📊 Engine Performance Comparison")
        print("=" * 60)
        
        print("Test queries for performance comparison:")
        print("1. Test with common .env file query")
        print("2. Test with configuration file query")
        print("3. Test with API endpoints query")
        print("4. Test with custom query")
        
        choice = input("\nSelect test type (1-4): ").strip()
        
        test_queries = {
            '1': 'site:github.com ".env" filetype:env',
            '2': 'site:github.com "config.json" "password"',
            '3': 'site:github.com "api" "endpoint"',
            '4': None
        }
        
        if choice in test_queries:
            if choice == '4':
                query = input("Enter custom query for testing: ")
            else:
                query = test_queries[choice]
            
            if query:
                print(f"\n🔍 Testing query: {query}")
                print("⏱️  Running performance comparison...")
                
                try:
                    # Get comparison results
                    comparison = self.credential_finder.cross_engine_search(query, num=10)
                    
                    # Display detailed comparison
                    self._display_detailed_engine_comparison(comparison, query)
                    
                    # Save results
                    save = input("\nSave comparison results? (y/n): ").lower()
                    if save == 'y':
                        safe_query = self._sanitize_filename(query, prefix="engine_comparison")
                        self.credential_finder.save_results(comparison, f'{safe_query}_comparison.json')
                        
                except Exception as e:
                    print(f"❌ Error during performance comparison: {e}")
    
    def _display_cross_engine_results(self, results, category):
        """Mostrar resultados multi‑motor con análisis detallado"""
        if not results:
            print(f"❌ No se encontraron resultados para {category}")
            return
        
        print(f"\n🔍 Resultados multi‑motor para {category}")
        print("=" * 80)
        
        # Resumen
        total_urls = results.get('total_unique_urls', 0)
        overlap = results.get('overlap_percentage', {})
        engines = results.get('engines_tested', [])
        
        print(f"📊 Total de URLs únicas encontradas: {total_urls}")
        print(f"🔍 Motores probados: {', '.join([e.value for e in engines])}")
        
        # Análisis de solapamiento
        if overlap:
            print(f"\n🔗 Análisis de solapamiento:")
            for engine, percentage in overlap.items():
                print(f"   {engine.value}: {percentage:.1%} de solapamiento con el total de resultados")
        
        # Mejores resultados combinados (deduplicados y ordenados) si están disponibles
        best_combined = results.get("best_combined")
        if best_combined:
            total_quality_score = results.get("total_quality_score", 0.0)
            print(f"\n🏆 Mejores resultados combinados (todos los motores)")
            print(f"📈 Puntuación de calidad global: {total_quality_score:.2f}")
            print("-" * 80)
            for i, result in enumerate(best_combined[:10], 1):  # mostrar top 10
                title = result.get("title", "N/A")
                link = result.get("link", "N/A")
                snippet = result.get("snippet", "N/A")[:120]
                quality = result.get("quality_score", 0.0)
                print(f"\n{i}. {title}")
                print(f"   URL: {link}")
                print(f"   Calidad: {quality:.2f}")
                print(f"   Resumen: {snippet}...")
        
        # Resultados combinados por motor
        combined_by_engine = results.get('combined_by_engine', {})
        if combined_by_engine:
            print(f"\n📈 Resultados por motor:")
            for engine_type, engine_results in combined_by_engine.items():
                print(f"   {engine_type.value}: {len(engine_results)} resultados")
    
    def _display_detailed_engine_comparison(self, comparison_results, query):
        """Display detailed engine performance comparison"""
        if not comparison_results:
            print("❌ No comparison data available")
            return
        
        print(f"\n📊 Detailed Engine Comparison for: {query[:50]}...")
        print("=" * 80)
        
        # Get results by engine
        results_by_engine = comparison_results.get('results_by_engine', {})
        
        if len(results_by_engine) < 2:
            print("❌ Need at least 2 engines for comparison")
            return
        
        # Calculate and display performance metrics
        print(f"\n🏆 Performance Summary:")
        for engine_type, results in results_by_engine.items():
            print(f"   {engine_type.value.title()}:")
            print(f"     - Results found: {len(results)}")
            print(f"     - Quality score: {self._calculate_result_quality(results):.2f}")
        
        # Show overlap analysis
        total_unique = comparison_results.get('total_unique_urls', 0)
        overlap = comparison_results.get('overlap_percentage', {})
        
        if total_unique > 0:
            print(f"\n🔗 Result Overlap Analysis:")
            print(f"   Total unique URLs: {total_unique}")
            for engine_type, percentage in overlap.items():
                print(f"   {engine_type.value}: {percentage:.1%} overlap")
        
        # Find common results
        print(f"\n🔍 Common Results (found by multiple engines):")
        common_count = sum(1 for p in overlap.values() if p > 0)
        print(f"   Common results found: {common_count}")
        
        # Recommendations
        best_engine = max(overlap.items(), key=lambda x: x[1])
        print(f"\n💡 Recommendations:")
        print(f"   Best overall coverage: {best_engine[0].value.title()}")
        
        if max(overlap.values()) < 0.5:
            print(f"   🔄 Consider using multiple engines for better coverage")
        else:
            print(f"   ✅ Good overlap between engines detected")
    
    def _calculate_result_quality(self, results):
        """Calculate quality score for a list of results"""
        if not results:
            return 0.0
        
        score = 0.0
        factors = 4
        
        # Factor 1: Results with snippets
        with_snippets = sum(1 for r in results if r.get('snippet', '').strip())
        score += with_snippets / len(results)
        
        # Factor 2: HTTPS results
        https_count = sum(1 for r in results if r.get('link', '').startswith('https://'))
        score += https_count / len(results)
        
        # Factor 3: Results from known domains
        reputable_domains = ['github.com', 'stackoverflow.com', 'docs.', 'wikipedia.org']
        reputable_count = sum(1 for r in results 
                            if any(domain in r.get('link', '') for domain in reputable_domains))
        score += reputable_count / len(results)
        
        # Factor 4: Results with meaningful titles
        meaningful_titles = sum(1 for r in results if len(r.get('title', '').strip()) > 10)
        score += meaningful_titles / len(results)
        
        return score / factors
    
    def pdf_book_search_menu(self):
        """Menu for advanced PDF book search using dork templates."""
        print("\n📚 PDF Book Search")
        print("=" * 60)
        
        while True:
            title = input("Enter book title (required, empty to return): ").strip()
            if not title:
                print("↩️  Returning to main menu...")
                break
            
            author = input("Author (optional): ").strip()
            topic = input("Topic/subject (optional, e.g. hacking, redes): ").strip()
            lang = input("Language hint (optional, e.g. es, en): ").strip()
            
            try:
                results = self.dork_engine.search_pdf_books(
                    title=title,
                    author=author or None,
                    topic=topic or None,
                    lang=lang or None,
                    num_per_dork=5,
                    verbose=True,
                )
                combined = results.get("combined", [])
                
                if not combined:
                    print("\n❌ No PDF results found for this search.")
                else:
                    # Para búsqueda de libros no necesitamos escanear cada URL en profundidad.
                    # Desactivamos temporalmente analyze_urls para evitar esperas largas.
                    old_gf = getattr(self.credential_finder, "global_filters", {}) or {}
                    gf_copy = old_gf.copy()
                    gf_copy["analyze_urls"] = False
                    self.credential_finder.global_filters = gf_copy

                    try:
                        self.credential_finder.display_results(combined, "PDF Book Search")
                    finally:
                        # Restaurar configuración original de filtros globales
                        self.credential_finder.global_filters = old_gf
                    
                    safe_title = self._sanitize_filename(title, prefix="pdf_books")
                    default_filename = f"pdf_books_{safe_title}.json"
                    self._save_generic_results(combined, default_filename)
            except Exception as e:
                print(f"❌ Error during PDF book search: {e}")
            
            again = input("\n🔁 Search another book? (y/n): ").strip().lower()
            if again != 'y':
                break
    
    def advanced_results_menu(self):
        """Menu for advanced result types: images, news, trending."""
        print("\n🖼️  Búsquedas avanzadas (imágenes / noticias / trending)")
        print("=" * 60)
        
        # Basic engine info
        try:
            engine_info = self.credential_finder.get_search_engine_info()
            current_engine = engine_info.get("engine_type") or "auto-select"
            print(f"🔍 Motor actual: {current_engine}")
        except Exception:
            print("🔍 Motor actual: desconocido")
        
        print("\nOpciones:")
        print("1. Buscar imágenes")
        print("2. Buscar noticias")
        print("3. Ver búsquedas en tendencia")
        print("4. Volver al menú principal")
        
        choice = input("\nSelecciona una opción (1-4): ").strip()
        
        if choice == '1':
            query = input("Consulta para imágenes: ").strip()
            if not query:
                print("❌ La consulta no puede estar vacía.")
                return
            try:
                results = self.credential_finder.search_manager.search_images(query, num=10)
                if not results:
                    print("❌ No se encontraron imágenes o el motor actual no soporta búsquedas de imágenes.")
                    return
                print(f"\n🖼️  Resultados de imágenes para: {query}")
                print("=" * 60)
                for i, r in enumerate(results[:10], 1):
                    print(f"\n{i}. {r.get('title', 'N/A')}")
                    print(f"   URL: {r.get('link', 'N/A')}")
                    thumb = r.get('thumbnail') or r.get('original')
                    if thumb:
                        print(f"   Thumbnail: {thumb}")
            except Exception as e:
                print(f"❌ Error al buscar imágenes: {e}")
        
        elif choice == '2':
            query = input("Consulta para noticias: ").strip()
            if not query:
                print("❌ La consulta no puede estar vacía.")
                return
            time_range = input("Rango de tiempo (opcional, p.ej. day, week, month, year): ").strip() or None
            try:
                results = self.credential_finder.search_manager.search_news(query, num=10, time_range=time_range)
                if not results:
                    print("❌ No se encontraron noticias o el motor actual no soporta búsquedas de noticias.")
                    return
                print(f"\n📰 Resultados de noticias para: {query}")
                print("=" * 60)
                for i, r in enumerate(results[:10], 1):
                    print(f"\n{i}. {r.get('title', 'N/A')}")
                    print(f"   URL: {r.get('link', 'N/A')}")
                    print(f"   Fecha: {r.get('date', 'N/A')}")
                    print(f"   Fuente: {r.get('source', 'N/A')}")
                    snippet = r.get('snippet') or ''
                    if snippet:
                        print(f"   Snippet: {snippet[:120]}...")
            except Exception as e:
                print(f"❌ Error al buscar noticias: {e}")
        
        elif choice == '3':
            region = input("Región (por defecto us-en, p.ej. es-es, en-us): ").strip() or "us-en"
            try:
                trends = self.credential_finder.search_manager.get_trending_searches(region)
                if not trends:
                    print("❌ No se pudieron obtener tendencias o el motor actual no las soporta.")
                    return
                print(f"\n📈 Búsquedas en tendencia para región: {region}")
                print("=" * 60)
                for i, q in enumerate(trends, 1):
                    print(f"{i}. {q}")
            except Exception as e:
                print(f"❌ Error al obtener tendencias: {e}")
        
        elif choice == '4':
            return
        else:
            print("❌ Opción inválida.")
    
    def api_keys_search_menu(self):
        """Menú para búsqueda de API keys de diferentes plataformas"""
        print("\n🔑 Búsqueda de API Keys - Todas las Plataformas")
        print("=" * 60)
        
        # Configuración de búsqueda
        num_results = 10
        
        while True:
            print("\nOpciones de búsqueda de API Keys:")
            print("1. 🤖 Buscar API Keys de OpenAI")
            print("2. 🐙 Buscar Tokens de GitHub")
            print("3. 💬 Buscar Tokens de Slack")
            print("4. 🔍 Buscar API Keys de Google")
            print("5. 💳 Buscar Tokens de Square")
            print("6. 🛒 Buscar Secretos de Shopify")
            print("7. 💰 Buscar Tokens de MercadoPago")
            print("8. 🌐 Buscar API Keys de TODAS las plataformas")
            print("9. 🔄 Búsqueda multi-motor de TODAS las plataformas")
            print("10. 🎯 Búsqueda personalizada de API key")
            print("11. ⚙️  Configurar número de resultados por búsqueda")
            print("12. Volver al menú principal")
            print(f"\n📊 Resultados por búsqueda: {num_results}")
            
            choice = input("\nSelecciona una opción (1-12): ").strip()
            
            if choice == '11':
                try:
                    new_num = input(f"Número de resultados por búsqueda (actual: {num_results}): ").strip()
                    if new_num:
                        num_results = max(1, min(100, int(new_num)))
                        print(f"✅ Configurado a {num_results} resultados por búsqueda")
                except ValueError:
                    print("❌ Valor inválido. Debe ser un número entre 1 y 100.")
                continue
            
            if choice == '1':
                print("\n🤖 Buscando API Keys de OpenAI...")
                # Guardar configuración anterior
                old_num = self.credential_finder.default_num_results
                self.credential_finder.default_num_results = num_results
                
                results = self.credential_finder.find_openai_api_keys()
                self.credential_finder.display_results(results, "API Keys de OpenAI")
                
                # Restaurar configuración
                self.credential_finder.default_num_results = old_num
                
                if results:
                    # Opción de buscar más
                    more = input("\n¿Buscar más resultados? (s/n): ").lower()
                    if more == 's':
                        continue
                    save = input("¿Guardar resultados? (s/n): ").lower()
                    if save == 's':
                        self.credential_finder.save_results(results, 'openai_api_keys_results.json')
            
            elif choice == '2':
                print("\n🐙 Buscando Tokens de GitHub...")
                old_num = self.credential_finder.default_num_results
                self.credential_finder.default_num_results = num_results
                
                results = self.credential_finder.find_github_tokens()
                self.credential_finder.display_results(results, "Tokens de GitHub")
                
                self.credential_finder.default_num_results = old_num
                
                if results:
                    more = input("\n¿Buscar más resultados? (s/n): ").lower()
                    if more == 's':
                        continue
                    save = input("¿Guardar resultados? (s/n): ").lower()
                    if save == 's':
                        self.credential_finder.save_results(results, 'github_tokens_results.json')
            
            elif choice == '3':
                print("\n💬 Buscando Tokens de Slack...")
                old_num = self.credential_finder.default_num_results
                self.credential_finder.default_num_results = num_results
                
                results = self.credential_finder.find_slack_tokens()
                self.credential_finder.display_results(results, "Tokens de Slack")
                
                self.credential_finder.default_num_results = old_num
                
                if results:
                    more = input("\n¿Buscar más resultados? (s/n): ").lower()
                    if more == 's':
                        continue
                    save = input("¿Guardar resultados? (s/n): ").lower()
                    if save == 's':
                        self.credential_finder.save_results(results, 'slack_tokens_results.json')
            
            elif choice == '4':
                print("\n🔍 Buscando API Keys de Google...")
                old_num = self.credential_finder.default_num_results
                self.credential_finder.default_num_results = num_results

                # Desactivar análisis profundo de URLs durante esta búsqueda
                # para evitar cuelgues al procesar cientos de resultados.
                old_gf = getattr(self.credential_finder, "global_filters", {}) or {}
                gf_copy = old_gf.copy()
                gf_copy["analyze_urls"] = False
                self.credential_finder.global_filters = gf_copy

                try:
                    results = self.credential_finder.find_google_api_keys()
                    self.credential_finder.display_results(results, "API Keys de Google")
                finally:
                    # Restaurar configuración original de filtros globales
                    self.credential_finder.global_filters = old_gf

                self.credential_finder.default_num_results = old_num

                if results:
                    more = input("\n¿Buscar más resultados? (s/n): ").lower()
                    if more == 's':
                        continue
                    save = input("¿Guardar resultados? (s/n): ").lower()
                    if save == 's':
                        self.credential_finder.save_results(results, 'google_api_keys_results.json')
            
            elif choice == '5':
                print("\n💳 Buscando Tokens de Square...")
                old_num = self.credential_finder.default_num_results
                self.credential_finder.default_num_results = num_results
                
                results = self.credential_finder.find_square_tokens()
                self.credential_finder.display_results(results, "Tokens de Square")
                
                self.credential_finder.default_num_results = old_num
                
                if results:
                    more = input("\n¿Buscar más resultados? (s/n): ").lower()
                    if more == 's':
                        continue
                    save = input("¿Guardar resultados? (s/n): ").lower()
                    if save == 's':
                        self.credential_finder.save_results(results, 'square_tokens_results.json')
            
            elif choice == '6':
                print("\n🛒 Buscando Secretos de Shopify...")
                old_num = self.credential_finder.default_num_results
                self.credential_finder.default_num_results = num_results
                
                results = self.credential_finder.find_shopify_secrets()
                self.credential_finder.display_results(results, "Secretos de Shopify")
                
                self.credential_finder.default_num_results = old_num
                
                if results:
                    more = input("\n¿Buscar más resultados? (s/n): ").lower()
                    if more == 's':
                        continue
                    save = input("¿Guardar resultados? (s/n): ").lower()
                    if save == 's':
                        self.credential_finder.save_results(results, 'shopify_secrets_results.json')
            
            elif choice == '7':
                print("\n💰 Buscando Tokens de MercadoPago...")
                old_num = self.credential_finder.default_num_results
                self.credential_finder.default_num_results = num_results
                
                results = self.credential_finder.find_mercadopago_tokens()
                self.credential_finder.display_results(results, "Tokens de MercadoPago")
                
                self.credential_finder.default_num_results = old_num
                
                if results:
                    more = input("\n¿Buscar más resultados? (s/n): ").lower()
                    if more == 's':
                        continue
                    save = input("¿Guardar resultados? (s/n): ").lower()
                    if save == 's':
                        self.credential_finder.save_results(results, 'mercadopago_tokens_results.json')
            
            elif choice == '8':
                print("\n🌐 Buscando API Keys en TODAS las plataformas...")
                old_num = self.credential_finder.default_num_results
                self.credential_finder.default_num_results = num_results
                
                results = self.credential_finder.find_all_api_keys()
                
                # Mostrar resultados por plataforma
                total_found = 0
                for platform, platform_results in results.items():
                    print(f"\n{'='*60}")
                    print(f"🔑 Resultados para {platform.upper()}: {len(platform_results)} encontrados")
                    print('='*60)
                    
                    if platform_results:
                        self.credential_finder.display_results(platform_results, f"API Keys - {platform.title()}")
                        total_found += len(platform_results)
                    else:
                        print(f"❌ No se encontraron resultados para {platform.upper()}")
                
                print(f"\n📊 Total de API keys encontradas: {total_found}")
                
                self.credential_finder.default_num_results = old_num
                
                # Guardar todos los resultados
                save = input("\n¿Guardar resultados de todas las plataformas? (s/n): ").lower()
                if save == 's':
                    self.credential_finder.save_results(results, 'all_api_keys_results.json')
            
            elif choice == '9':
                print("\n🔄 Búsqueda multi-motor de API Keys en TODAS las plataformas...")
                old_num = self.credential_finder.default_num_results
                self.credential_finder.default_num_results = num_results
                
                results = self.credential_finder.find_all_api_keys_cross_engine()
                
                # Mostrar resultados multi-motor por plataforma
                total_unique = 0
                for platform, platform_results in results.items():
                    print(f"\n{'='*60}")
                    print(f"🔍 Resultados multi-motor para {platform.upper()}")
                    print('='*60)
                    
                    if isinstance(platform_results, dict) and platform_results.get('total_unique_urls', 0) > 0:
                        self.credential_finder.display_results(
                            platform_results, 
                            f"API Keys {platform.title()} (Multi-Motor)", 
                            is_cross_engine=True
                        )
                        total_unique += platform_results.get('total_unique_urls', 0)
                    else:
                        print(f"❌ No se encontraron resultados para {platform.upper()}")
                
                print(f"\n📊 Total de URLs únicas encontradas: {total_unique}")
                
                self.credential_finder.default_num_results = old_num
                
                # Guardar resultados multi-motor
                save = input("\n¿Guardar resultados multi-motor de todas las plataformas? (s/n): ").lower()
                if save == 's':
                    self.credential_finder.save_results(results, 'all_api_keys_cross_engine_results.json')
            
            elif choice == '10':
                print("\n🎯 Búsqueda personalizada de API key")
                platform_name = input("Nombre de la plataforma (ej: AWS, Azure, Stripe): ").strip()
                if not platform_name:
                    print("❌ El nombre de la plataforma no puede estar vacío.")
                    continue
                
                key_pattern = input("Patrón de la clave (ej: AKIA, sk_live_, etc.) o Enter para omitir: ").strip()
                
                # Construir query personalizada
                if key_pattern:
                    custom_query = f'site:github.com ("{key_pattern}" AND {platform_name})'
                else:
                    custom_query = f'site:github.com ("{platform_name}" AND ("api_key" OR "secret" OR "token"))'
                
                print(f"\n🔍 Ejecutando búsqueda: {custom_query}")
                
                use_cross_engine = input("¿Usar búsqueda multi-motor? (s/n): ").lower() == 's'
                
                if use_cross_engine:
                    results = self.credential_finder.cross_engine_search(custom_query, num=num_results)
                    self.credential_finder.display_results(
                        results, 
                        f"API Keys de {platform_name} (Multi-Motor)", 
                        is_cross_engine=True
                    )
                else:
                    results = self.credential_finder.search(custom_query, num_results)
                    results = self.credential_finder.apply_advanced_filters(
                        results, 
                        [platform_name.lower(), 'api', 'key', 'secret', 'token']
                    )
                    self.credential_finder.display_results(results, f"API Keys de {platform_name}")
                
                if results:
                    save = input("\n¿Guardar resultados? (s/n): ").lower()
                    if save == 's':
                        safe_name = self._sanitize_filename(platform_name, prefix="api_keys")
                        filename = f'{safe_name}_api_keys_results.json'
                        self.credential_finder.save_results(results, filename)
            
            elif choice == '12':
                return
             
            else:
                print("❌ Opción inválida. Por favor selecciona un número entre 1 y 12.")
      
    def smart_search_menu(self):
        """Interactive regex-based search over local result files using SmartSearch."""
        print("\n🔎 SmartSearch sobre resultados locales")
        print("=" * 60)

        base_dir = input("Directorio base para buscar (Enter = directorio actual): ").strip()
        if not base_dir:
            base_dir = os.getcwd()

        rec_input = input("¿Buscar recursivamente en subdirectorios? (s/n, Enter = s): ").strip().lower()
        recursive = rec_input not in ("n", "no")

        profile_input = input(
            "¿Usar perfil rápido de archivos de resultados del kit? (s/n, Enter = s): "
        ).strip().lower()

        if profile_input in ("", "s", "y", "sí", "si"):
            file_patterns = [
                "*results*.json",
                "*_results.json",
                "*cross_engine*.json",
                "*report*.json",
                "*.txt",
            ]
        else:
            raw_patterns = input(
                "Patrones de archivo (glob) separados por coma (ej: *.json,*.txt). Enter = todos: "
            ).strip()
            file_patterns = [p.strip() for p in raw_patterns.split(",") if p.strip()] if raw_patterns else []

        regex = input("Expresión regular a buscar (obligatoria): ").strip()
        if not regex:
            print("❌ La expresión regular no puede estar vacía.")
            return

        cs_input = input("¿Distinguir mayúsculas/minúsculas? (s/n, Enter = n): ").strip().lower()
        case_sensitive = cs_input in ("s", "y", "sí", "si")

        from typing import Optional

        def _read_int(prompt: str, default: Optional[int]) -> Optional[int]:
            value = input(prompt).strip()
            if not value:
                return default
            try:
                return int(value)
            except ValueError:
                print("   ⚠️  Valor no válido, se usará el valor por defecto.")
                return default

        context_lines = _read_int("Líneas de contexto antes/después de cada match (Enter = 2): ", 2)
        max_size_mb = _read_int("Tamaño máximo de archivo en MB (Enter = 5): ", 5)
        max_matches_per_file = _read_int(
            "Máximo de coincidencias por archivo (Enter = sin límite): ", None
        )

        try:
            searcher = SmartSearch(
                dir_path=base_dir,
                file_patterns=file_patterns,
                recursive=recursive,
                max_file_size_mb=max_size_mb or 5,
                ignore_binary=True,
            )
        except Exception as e:
            print(f"❌ Error al inicializar SmartSearch: {e}")
            return

        try:
            results = searcher.regex_search(
                pattern=regex,
                case_sensitive=case_sensitive,
                multiline=True,
                context_lines=context_lines or 2,
                max_matches_per_file=max_matches_per_file,
            )
        except ValueError as e:
            print(f"❌ Error en la expresión regular: {e}")
            return
        except Exception as e:
            print(f"❌ Error durante la búsqueda: {e}")
            return

        summary = results.get("summary", {})
        print("\n📊 Resumen de SmartSearch:")
        print(f"   Archivos escaneados: {summary.get('total_files_scanned', 0)}")
        print(f"   Archivos con coincidencias: {summary.get('total_files_with_matches', 0)}")
        print(f"   Coincidencias totales: {summary.get('total_matches', 0)}")

        matches = results.get("matches") or []
        if not matches:
            print("\n✅ No se encontraron coincidencias.")
            return

        print("\n🔍 Detalle de coincidencias:")
        print("=" * 60)
        for file_result in matches:
            print(f"\n📄 Archivo: {file_result.get('file')} ")
            print(f"   Ruta: {file_result.get('path')}")
            print(f"   Coincidencias: {file_result.get('match_count', 0)}")

            for m in file_result.get("matches", []):
                line_no = m.get("line_number")
                context_line = m.get("context_line", "")
                print(f"   - Línea {line_no}: {context_line}")
                before = m.get("context_before") or []
                after = m.get("context_after") or []
                if before or after:
                    print("     Contexto:")
                    for ctx in before:
                        print(f"       < {ctx}")
                    print(f"       = {context_line}")
                    for ctx in after:
                        print(f"       > {ctx}")

        # Aplanar resultados para permitir guardarlos fácilmente en JSON
        flat_results = []
        for file_result in matches:
            file_name = file_result.get("file")
            file_path = file_result.get("path")
            for m in file_result.get("matches", []):
                flat_results.append(
                    {
                        "file": file_name,
                        "path": file_path,
                        "line_number": m.get("line_number"),
                        "match_text": m.get("match_text"),
                        "context_before": m.get("context_before"),
                        "context_line": m.get("context_line"),
                        "context_after": m.get("context_after"),
                    }
                )

        if flat_results:
            print("\n💾 Puedes guardar estos resultados en un JSON para analizarlos después.")
            self._save_generic_results(flat_results, "smart_search_results.json")
      
    def llm_dork_assistant_menu(self):
        """Menú para interactuar con el LLM de Groq para generación y análisis de dorks."""
        print("\n🤖 Asistente LLM de Dorks (Groq)")
        print("=" * 60)

        # Inicializar el asistente solo cuando se use
        if self.llm_dork_assistant is None:
            try:
                self.llm_dork_assistant = GroqDorkAssistant()
            except Exception as e:
                print(f"❌ No se pudo inicializar el asistente LLM: {e}")
                print("   Asegúrate de tener GROQ_API_KEY configurada en tu .env")
                return

        while True:
            print("\nOpciones del asistente LLM:")
            print("1. Generar dorks a partir de un prompt")
            print("2. Explicar un dork existente")
            print("3. Sugerir dorks relacionados a partir de un dork")
            print("4. Volver al menú principal")

            choice = input("\nSelecciona una opción (1-4): ").strip()

            if choice == '1':
                prompt = input("\nDescribe qué quieres encontrar (en lenguaje natural): ").strip()
                if not prompt:
                    print("❌ El prompt no puede estar vacío.")
                    continue
                engine = input("Motor preferido (google/duckduckgo, Enter = google): ").strip().lower() or "google"
                print("\n🧨 Dorks sugeridos por el LLM:\n")
                # No usamos streaming aquí para poder reutilizar las líneas
                raw = self.llm_dork_assistant.generate_dorks_from_prompt(
                    prompt,
                    engine=engine,
                    stream=False,
                )
                dorks = [line.strip() for line in raw.splitlines() if line.strip()]
                if not dorks:
                    print("❌ El modelo no devolvió ningún dork utilizable.")
                    continue

                for i, dq in enumerate(dorks, 1):
                    print(f"{i}. {dq}")

                # Opción rápida para ejecutar uno de los dorks
                run_choice = input("\n¿Quieres ejecutar alguno de estos dorks ahora? (número / Enter = no): ").strip()
                if run_choice.isdigit():
                    idx = int(run_choice)
                    if 1 <= idx <= len(dorks):
                        selected_dork = dorks[idx - 1]
                        use_cross = input("¿Usar búsqueda multi-motor? (s/n, Enter = n): ").strip().lower() in ("s", "y")
                        print(f"\n🔍 Ejecutando dork generado:\n{selected_dork}\n")
                        try:
                            results = self.credential_finder.dork_search(selected_dork, use_cross_engine=use_cross)
                            if use_cross:
                                self.credential_finder.display_results(
                                    results,
                                    "Dork LLM (multi-motor)",
                                    is_cross_engine=True,
                                )
                            else:
                                self.credential_finder.display_results(
                                    results,
                                    "Dork LLM",
                                )
                        except Exception as e:
                            print(f"❌ Error al ejecutar el dork generado: {e}")

            elif choice == '2':
                dork = input("\nPega el dork que quieres que el LLM analice: ").strip()
                if not dork:
                    print("❌ El dork no puede estar vacío.")
                    continue
                print("\n📖 Explicación del dork:\n")
                self.llm_dork_assistant.explain_dork(dork, stream=True)

            elif choice == '3':
                dork = input("\nPega el dork base a partir del cual quieres variantes: ").strip()
                if not dork:
                    print("❌ El dork no puede estar vacío.")
                    continue
                print("\n🧨 Dorks relacionados sugeridos por el LLM:\n")
                self.llm_dork_assistant.suggest_related_dorks(dork, stream=True)

            elif choice == '4':
                return
            else:
                print("❌ Opción inválida.")
    def generate_reports_menu(self):
        """Generate reports menu"""
        print("\n� Report Generation")
        print("=" * 50)
        
        print("Available options:")
        print("1. Generate report from JSON files")
        print("2. Generate comprehensive report")
        
        choice = input("Enter choice: ").strip()
        
        if choice == '1':
            from report_generator import main as report_main
            report_main()
        elif choice == '2':
            self.report_generator.generate_comprehensive_report()
    
    def global_engine_configuration_menu(self):
        """Global search engine configuration menu"""
        print("\n⚙️  Configuración Global del Motor de Búsqueda")
        print("=" * 60)

        # Show current global engine info
        global_info = self.get_global_engine_info()
        print(f"🌐 Configuración Global Actual:")
        print(f"   Motor Preferido: {global_info.get('global_preference', 'Desconocido')}")
        print(f"   Motor del Buscador de Credenciales: {global_info.get('credential_finder_engine', 'Desconocido')}")
        print(f"   Motores Disponibles: {', '.join(global_info.get('available_engines', []))}")
        print(f"   Optimizador de Consultas: {'✅ Disponible' if global_info.get('query_optimizer_available') else '❌ No Disponible'}")

        while True:
            print("\nOpciones de Configuración:")
            print("1. Establecer Google como motor global")
            print("2. Establecer DuckDuckGo como motor global")
            print("3. Establecer Selenium como motor global")
            print("4. Habilitar auto-selección (mejor motor disponible)")
            print("5. Probar configuración del motor")
            print("6. Mostrar consejos de optimización del motor")
            print("7. Volver al menú principal")

            choice = input("\nSelecciona opción (1-7): ").strip()

            if choice == '1':
                self.set_global_search_engine(SearchEngineType.GOOGLE)
                print("✅ Google establecido como motor global para todas las herramientas")

            elif choice == '2':
                self.set_global_search_engine(SearchEngineType.DUCKDUCKGO)
                print("✅ DuckDuckGo establecido como motor global para todas las herramientas")

            elif choice == '3':
                self.set_global_search_engine(SearchEngineType.SELENIUM_GOOGLE)
                print("✅ Selenium establecido como motor global para todas las herramientas")

            elif choice == '4':
                self.set_global_search_engine(None)  # Auto-select
                print("✅ Auto-selección habilitada para todas las herramientas")

            elif choice == '5':
                self._test_engine_configuration()

            elif choice == '6':
                self._show_engine_tips()

            elif choice == '7':
                break

            else:
                print("❌ Opción inválida. Por favor selecciona un número entre 1 y 7.")
    
    def _test_engine_configuration(self):
        """Test current engine configuration"""
        print("\n🧪 Probando Configuración del Motor...")

        try:
            # Test CredentialFinder engine
            cred_info = self.credential_finder.get_search_engine_info()
            print(f"✅ Motor de CredentialFinder: {cred_info.get('engine_type', 'Desconocido')}")
            print(f"   Disponible: {', '.join(cred_info.get('available_engines', []))}")

            # Test DorkEngine engine
            dork_info = self.dork_engine.get_engine_info()
            print(f"✅ Motor de DorkEngine: {dork_info.get('current_engine', 'Desconocido')}")

            # Test with a simple query
            test_query = "site:github.com test"
            print(f"\n🔍 Probando con consulta: {test_query}")

            try:
                results = self.credential_finder.search(test_query, num=3)
                print(f"✅ Búsqueda exitosa: {len(results)} resultados encontrados")

            except Exception as e:
                print(f"❌ Búsqueda fallida: {e}")

        except Exception as e:
            print(f"❌ Prueba de configuración del motor fallida: {e}")
    
    def _show_engine_tips(self):
        """Show engine-specific optimization tips"""
        if not self.query_optimizer:
            print("❌ Optimizador de consultas no disponible")
            return

        print("\n💡 Consejos de Optimización del Motor")
        print("=" * 50)

        # Show Google tips
        print("\n🔍 Consejos para Búsqueda en Google:")
        google_tips = self.query_optimizer.get_engine_specific_tips(SearchEngineType.GOOGLE)
        for i, tip in enumerate(google_tips, 1):
            print(f"  {i}. {tip}")

        # Show DuckDuckGo tips
        print("\n🦆 Consejos para Búsqueda en DuckDuckGo:")
        ddg_tips = self.query_optimizer.get_engine_specific_tips(SearchEngineType.DUCKDUCKGO)
        for i, tip in enumerate(ddg_tips, 1):
            print(f"  {i}. {tip}")

        # Query optimization analysis
        print("\n🔧 Análisis de Optimización de Consultas:")
        test_queries = [
            'site:github.com filetype:env "password"',
            'site:github.com "config.json" "api_key"',
            'site:github.com intitle:admin "login"'
        ]

        for query in test_queries:
            compatibility = self.query_optimizer.analyze_query_compatibility(query)
            print(f"\n  Consulta: {query[:40]}...")
            print(f"    Recomendación: {compatibility['recommendation']}")

    def show_settings(self):
        """Show configuration settings"""
        print("\n⚙️  Configuration Settings")
        print("=" * 60)
        
        # Check environment variables
        api_key = os.getenv('API_KEY_GOOGLE')
        engine_id = os.getenv('SEARCH_ENGINE_ID')
        serp_api_key = os.getenv('SERP_API_KEY')
        serper_api_key = os.getenv('SERPER_API_KEY')
        
        print(f"🔍 Search Engine Configuration:")
        print(f"   Google API Key: {'✅ Configured' if api_key else '❌ Missing'}")
        print(f"   Search Engine ID: {'✅ Configured' if engine_id else '❌ Missing'}")
        print(f"   SerpAPI Key: {'✅ Configured' if serp_api_key else '❌ Missing'}")
        print(f"   Serper API Key: {'✅ Configured' if serper_api_key else '❌ Missing'}")
        
        if not api_key or not engine_id:
            print("\n⚠️  Missing Google API configuration!")
            print("Update your .env file with:")
            print("API_KEY_GOOGLE=your_google_api_key")
            print("SEARCH_ENGINE_ID=your_search_engine_id")
        
        if not serp_api_key:
            print("\n⚠️  Missing SerpAPI configuration!")
            print("Update your .env file with:")
            print("SERP_API_KEY=your_serpapi_key")
        
        # Show current engine status
        try:
            cred_info = self.credential_finder.get_search_engine_info()
            global_info = self.get_global_engine_info()
            print(f"\n🔧 Current Configuration:")
            print(f"   Global Preference: {global_info.get('global_preference', 'Unknown')}")
            print(f"   Active Engine: {cred_info['engine_type'].title() if cred_info['engine_type'] else 'Auto-select'}")
            print(f"   Available Engines: {', '.join(cred_info['available_engines'])}")
        except Exception as e:
            print(f"   Error getting engine info: {e}")
        
        print(f"\n🛠️  System Information:")
        print(f"   Working Directory: {os.getcwd()}")
        print(f"   Python Version: {sys.version}")
        print(f"   Query Optimizer: {'✅ Available' if self.query_optimizer else '❌ Not Available'}")
    
    def show_help(self):
            """Mostrar ayuda y documentación en español"""
            help_text = """
     📚 AYUDA Y DOCUMENTACIÓN
     =========================
     
     VISIÓN GENERAL
     --------------
     Este kit te ayuda a descubrir posibles problemas de seguridad encontrando:
     
     • Credenciales expuestas
     • Archivos sensibles (.env, archivos de configuración, backups)
     • Endpoints de API y documentación
     • Subdominios y servicios expuestos
     
     Lo hace combinando:
     • Dorking multi‑motor (Google + DuckDuckGo vía SerpAPI)
     • Búsquedas especializadas en GitHub
     • Descubrimiento de subdominios y generación de reportes
     
     HERRAMIENTAS PRINCIPALES
     ------------------------
     • Credential Finder
       - Búsquedas específicas de:
         · Archivos .env
         · Archivos de configuración
         · Credenciales (tokens, claves, contraseñas)
         · Endpoints de API
       - Soporta:
         · Un solo motor (Google o DuckDuckGo)
         · Búsqueda multi‑motor (cross‑engine)
         · Comparación de motores (quality_score)
     
     • Dork Engine
       - Ejecuta dorks avanzados definidos en dorks_catalog.json
       - Permite:
         · Ejecutar categorías completas de dorks con un solo motor
         · Ejecutar dorks en modo multi‑motor y ver resultados combinados
         · Buscar libros y recursos PDF mediante la categoría pdf_books
     
     • Subdomain Finder
       - Descubrimiento de subdominios:
         · Fuerza bruta DNS
         · Búsqueda en motores
         · Transparencia de certificados
       - Opcionalmente, escaneo básico de puertos
     
     • Report Generator
       - Crea reportes en:
         · HTML
         · Texto plano
         · JSON
       - Incluye resumen de riesgo y categorización de hallazgos.
     
     • Master Tool (este menú)
       - Orquesta todas las herramientas en una sola interfaz:
     
         1. Buscador de credenciales (interactivo)
         2. Descubrimiento de subdominios
         3. Plantillas de Google Dorking
         4. Dorks avanzados multi‑motor (Google + DuckDuckGo)
         5. Búsqueda de libros PDF
         6. Búsqueda cruzada entre motores (credenciales/config/API)
         7. Generación de reportes
         8. Escaneo rápido (todas las herramientas)
         9. Configuración global de motores
        10. Comparación de rendimiento entre motores
        11. Ayuda y documentación (este texto)
        12. Búsquedas avanzadas de imágenes / noticias / trending (DuckDuckGo)
        13. Dorks interactivos (selección personalizada)
        14. Modo cámaras (dorks personalizados)
        15. Búsqueda de API Keys (OpenAI, GitHub, Slack, Google, Square, Shopify)
        16. Asistente LLM de dorks (Groq)
        17. SmartSearch sobre resultados locales
        18. Salir
     
     INTERFAZ MULTI‑MOTOR
     --------------------
     Bajo el menú, la lógica de búsquedas se basa en una interfaz unificada:
     
     • SearchEngineInterface
       - Define el contrato para motores de búsqueda:
         · search(), extract_results(), display_results()
         · search_images(), search_news(), get_trending_searches()
         · search_with_fallback() (reintentos con parámetros reducidos)
     
     • UnifiedSearchManager
       - Registra motores (Google, DuckDuckGo via SerpAPI)
       - Permite:
         · Seleccionar el motor actual
         · Buscar con fallback transparente
         · Ejecutar una misma consulta en varios motores y comparar resultados
     
     • QueryOptimizer / EngineAwareSearchManager
       - Analizan cada consulta y la ajustan según el motor:
         · Limpian operadores que DuckDuckGo no soporta o no aprovecha bien
         · Mantienen dorks avanzados ricos para Google cuando tiene sentido
       - Se usan tanto en CredentialFinder como en DorkEngine para las búsquedas
         multi‑motor y las comparaciones de rendimiento.
     
     MÉTRICAS EN LOS RESULTADOS
     --------------------------
     En las listas de resultados verás, además del título/URL/snippet, varias
     métricas numéricas:
     
     • quality_score
       - Indica la “calidad” aparente de cada resultado:
         · Tiene snippet
         · Título con sentido
         · URL HTTPS
         · Dominio reputado (github, docs, wikipedia, etc.)
     
     • risk_score
       - Indica de forma HEURÍSTICA cuán “sensibles” parecen los datos:
         · Tipo de fichero asociado a configs/credenciales (.env, .config, .yml, .php, .json, etc.)
         · Palabras clave de credenciales (password, secret, token, api_key, access_key, private key, etc.)
         · Dominio: recursos fuera de GitHub/GitLab se consideran algo más riesgosos
     
       Importante:
       - Se usa sobre todo para priorizar hallazgos de credenciales/config.
       - Si estás buscando libros PDF, risk_score NO evalúa copyright ni legalidad;
         simplemente aplica la misma heurística técnica, que en muchos casos será baja.
     
     CONSEJOS DE USO
     ---------------
     • Para una visión rápida de un dominio:
       - Usa el Escaneo rápido (opción 8).
       - Revisa luego los reportes HTML/TXT/JSON que se generan automáticamente.
     
     • Para investigación detallada:
       - Empieza con Descubrimiento de subdominios (opción 2).
       - Usa Credential Finder (opción 1) para credenciales/config/APIs.
       - Usa Dork Engine (opción 4/5) para dorks avanzados y búsqueda de libros PDF.
     
     • Multi‑motor:
       - Configura el motor global en la opción 9:
         · Google
         · DuckDuckGo
         · Auto‑select (elige el mejor disponible según lo configurado)
       - Explora la opción 6 y 10 para ver cómo se comportan los motores y qué
         cobertura ofrece cada uno.
     
     REQUISITOS
     ----------
     • Python 3.6 o superior
     • Clave de API de Google Custom Search (para usar Google)
     • Clave de SerpAPI (para usar DuckDuckGo vía SerpAPI)
     • Conexión a Internet
     • Dependencias indicadas en requirements.txt (requests, dnspython, python-dotenv, etc.)
     
     AVISO LEGAL Y USO ÉTICO
     -----------------------
     ⚠️  IMPORTANTE:
         Usa esta herramienta SOLO en:
         • Sistemas que te pertenezcan, o
         • Sistemas para los que tengas permiso explícito y por escrito.
     
     El uso no autorizado contra sistemas de terceros es ilegal.
     
     Buenas prácticas:
     • Respeta las políticas de uso y límites de cada servicio.
     • No explotes vulnerabilidades; limítate a identificarlas.
     • Usa los reportes para mejorar la seguridad, no para atacar.
     • Sigue marcos de trabajo autorizados (pentesting con contrato, programas de Bug Bounty, etc.).
     
     PARA SABER MÁS
     --------------
     Consulta también el archivo README.md del proyecto, donde se detalla:
     
     • Arquitectura multi‑motor
     • Catálogo de dorks avanzados
     • Ejemplos de uso
     • Recomendaciones adicionales y recursos externos
     
     by Roska
     
     """
            print(help_text)

def main():
    """Bucle principal de la aplicación"""
    tool = MasterSecurityTool()
    
    while True:
        try:
            tool.show_banner()
            tool.show_menu()
            
            choice = input("\nSelecciona una opción (1-18): ").strip()
            
            if choice == '1':
                tool.credential_finder_menu()
            
            elif choice == '2':
                tool.subdomain_discovery_menu()
            
            elif choice == '3':
                tool.dorking_templates_menu()
            
            elif choice == '4':
                tool.advanced_dorks_multi_engine_menu()
            
            elif choice == '5':
                tool.pdf_book_search_menu()
            
            elif choice == '6':
                tool.cross_engine_search_menu()
            
            elif choice == '7':
                tool.generate_reports_menu()
            
            elif choice == '8':
                tool.quick_scan()
            
            elif choice == '9':
                tool.global_engine_configuration_menu()
            
            elif choice == '10':
                tool.engine_performance_comparison_menu()
            
            elif choice == '11':
                tool.show_help()

            elif choice == '12':
                tool.advanced_results_menu()

            elif choice == '13':
                tool.interactive_dorks_menu()

            elif choice == '14':
                tool.cameras_mode_menu()

            elif choice == '15':
                tool.api_keys_search_menu()

            elif choice == '16':
                tool.llm_dork_assistant_menu()

            elif choice == '17':
                tool.smart_search_menu()

            elif choice == '18':
                print("\n👋 ¡Gracias por usar el Kit Avanzado de Descubrimiento de Credenciales!")
                print("   by Roska")
                print("🔒 Recuerda: utiliza esta herramienta de forma responsable y ética.")
                print('''################+++++++++++++++++++++----------....
    +  #+  ##  #    ## +   +      +   -  +-------
    #   +  ##   #   ## +   +  + + # +  +     ---
 #############+++++++++++++++++++++++++----------
 ##############+++++++++++++++++++++++-++++-----+       ...  .
    #  #   #     +## +  +.   + ++##   +  -++++--.   .
 ##### ########++++++++++++++++-+++-#.++-------.-
 ##########++++++++++++++.####    ##   ## ------- .     .+-
 ##### ## #+   #    ###                    #+#--.              -.                                         .   .
   ##   #   ++ +##                             ##
 #######+##+##                                    #
 ######+++##                                        #
  #.#  #+#                                            #
 # ######                                              #
 ######+#                                                #
 #######                                                  #
  ###  #                                                   #
 #######                       # #                          #                                             ..
 #######        ##+##########                               # .                                               .
 #  #  #   ##                     ####                       #
 #  + ####                              ###                  #
 #################        ######################            #                                                -
 ####+++++-  +#+#   #    ##+ -+   #++++++   #-+###          #                                              ..-
 #  #++++# ++ +  ##+##  ##+++#+  +++++++  #-++--#####      #              ..
 #####++ #++-    +++######++ #  ++++++    +++++########-  +                                           .
 ###### ++#+  #+++++######+   +++++++  #+++-+++#    ######                                               .   .
  # +##+++    +++++ ##  ##+  ++++++    -+++++-##     ###- #
    # #+#  #++++++ .#   ####++++++  #++++++++-#      ##### #                                              .   .
 #######  ++++++- ###    ##+++++    +++++++++##     ####### ##                                  .          +
  #######++++++ ++.#+     ##+++  #+++++++++-##     #######                                                    .
 ######+-###########      ###    +++++++-####
 ########+++ #####           #############                                          .              -.      -  -
 ########++++#      #  +                                                             . .-   --- --  .    -  ..
 ##### #++++++                                  #  +############
 ####+##+##+ -#                                # -    + +          .               -+ ..         - - +  --  .
 #######++++##+#           ##++               #                                             .   -  .   -
 - #   +#+  # + #                           ##                                                                .
 ######+##+++++++#                        +###  - -  -+-..-..   .----   . -                                ....
 #######++++++++++#-                    ###+#.   --         .   .---                  +      +  .      +++-. ..
   #   ##     + #   #                 ####  #. .                                    - - .+-  .- .      +++-....
 # #   +#   + ###    #             ######- ##    ###### .                                               .......
 ############+#+++++++##       ####### --  ###.......- . # .          -                - .   +        .      ..
 ##########+#++++++++++++#########--.-     ############+ +##                           - - - .   .   .    +  ..
  #- # #   # +   #+ ++  # ###---#          ###########-     #      .                                  ........
 ###  ## #.#######+#++###--#+####           ########.        #                                         ........
 ###############++++##---#########            ###+.           #                          --  -- .-++-...++++...
 ##############+#.+##----.########         ##-.  . +           #                     .  -  - .  .-+++...... -..
  ##   + # + # + # ###---- ######      ###+   + + - +#+#.### . +  --..  --                     ...............-
 ###############++++####---. ###    ## +.    - ##   ### .  -####. .   - .-             .  -+  .    -      -
 ################++++###..-.   ####      -##    ####-     . ####                       .   - +.   .+ .    - +
 #   #   +    # #+++#--# #-+ ... #-.+. -    #### ..     #     # # . .              .....-............-.--------
 ################++#-----# ##.. #.. #   ##-#  ..-.    #        .##. .   .. ..... ...............-..------------
 ################+#.------  ##..... ###+-+    ...-#  #-.    .   +# ..     ..........-++-.    -.-   +++#++#+ +
 +#  +   # # # # +##------- --.###+ -. ........ .##..# . . ... . -#  .   - .........+++-.++- -.- - -##  +#+-+.+
 ### #   #.# # # #-#------- ----..  .... .......  #. ... .... .  -# ..  -  ---..............-.---#.--.  #---#--
 #################-#--.          ++.     +-#+... -#.#.............##-......-----.--.    --  -   -   -    #  -
 ################-#---#   ##.   ..## #       .....#.#-............-# ...-..---------+   --  .   + #-      # +++
 ##.##  ##   # #+-#----    #       .      -. .....#.#-...........  ##  .   -----------------------+   +-   +-++
 ###############--#--+ .      ....        ++#.....-##--...........  #      ---------------------------+#--+++++
 ###############-+--....-    -....    # +#    .... ##--............-#.--------------+  #+--##+   +  + +#   + ++
''')
                break
            
            else:
                print("\n❌ Opción inválida. Por favor selecciona un número entre 1 y 18.")
            
            input("\nPulsa Enter para continuar...")
            
        except KeyboardInterrupt:
            print("\n\n👋 ¡Hasta luego!")
            break
        except Exception as e:
            print(f"\n❌ Se produjo un error: {e}")
            input("Pulsa Enter para continuar...")

if __name__ == "__main__":
 main()
