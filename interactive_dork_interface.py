#!/usr/bin/env python3
"""
Interactive Dork Interface - Allows users to select specific dorks and provides pagination
Enhanced OSINT and camera customization options
"""

import os
import json
from typing import Dict, List, Any, Optional, Tuple
from search_engine_interface import SearchEngineType
from dork_catalog import DorkCatalog
from dork_engine import DorkEngine


class InteractiveDorkInterface:
    """Interactive interface for selecting and executing individual dorks with pagination"""
    
    def __init__(self, dork_engine: DorkEngine):
        """Initialize with a DorkEngine instance"""
        self.dork_engine = dork_engine
        self.catalog = DorkCatalog()
        self.results_cache = {}  # Cache for pagination
        self.current_page = 1
        self.results_per_page = 10
        
    def show_categories_menu(self) -> Optional[str]:
        """Show categories and allow user selection"""
        categories = self.catalog.get_categories()
        
        if not categories:
            print("❌ No se encontraron categorías de dorks")
            return None
        
        print("\n🧨 Dorks Interactivos - Selección Personalizada")
        print("=" * 60)
        print("Categorías disponibles:")
        
        for idx, cat in enumerate(categories, 1):
            dorks_in_cat = len(self.catalog.get_by_category(cat))
            print(f"{idx:2d}. {cat.replace('_', ' ').title()} ({dorks_in_cat} dorks)")
        print("  0. Volver al menú principal")
        
        while True:
            choice = input("\nSelecciona una categoría (número): ").strip()
            
            if choice == '0':
                return None
            
            try:
                idx = int(choice)
                if 1 <= idx <= len(categories):
                    return categories[idx - 1]
                else:
                    print("❌ Número fuera de rango. Intenta de nuevo.")
            except ValueError:
                print("❌ Introduce un número válido.")
    
    def show_dorks_in_category(self, category: str) -> List[Dict[str, Any]]:
        """Show all dorks in a category for user selection"""
        dorks = self.catalog.get_by_category(category)
        
        if not dorks:
            print(f"❌ No se encontraron dorks en la categoría: {category}")
            return []
        
        print(f"\n📋 Dorks disponibles en: {category.replace('_', ' ').title()}")
        print("=" * 80)
        
        for idx, dork in enumerate(dorks, 1):
            title = dork.get('title', 'Sin título')
            query = dork.get('query', '')
            risk = dork.get('risk', 'unknown')
            tags = ', '.join(dork.get('tags', []))
            
            # Color coding for risk levels
            risk_colors = {
                'high': '🔴',
                'medium': '🟡', 
                'low': '🟢',
                'info': '🔵'
            }
            risk_icon = risk_colors.get(risk, '⚪')
            
            print(f"\n{idx:2d}. {risk_icon} {title}")
            print(f"    Query: {query}")
            print(f"    Risk: {risk.title()} | Tags: {tags}")
        
        return dorks
    
    def select_dorks(self, dorks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Allow user to select specific dorks to run"""
        print(f"\n🎯 Selección de Dorks")
        print("=" * 50)
        print("Opciones de selección:")
        print("• Escribe números separados por coma (ej: 1,3,5)")
        print("• Rango con guiones (ej: 1-5)")
        print("• 'all' para ejecutar todos")
        print("• 'none' para volver")
        
        selection = input("\nTu selección: ").strip().lower()
        
        if selection == 'none':
            return []
        elif selection == 'all':
            return dorks
        elif '-' in selection:
            # Range selection
            try:
                start, end = map(int, selection.split('-'))
                if 1 <= start <= end <= len(dorks):
                    return dorks[start-1:end]
                else:
                    print("❌ Rango fuera de límites.")
                    return []
            except ValueError:
                print("❌ Formato de rango inválido.")
                return []
        elif ',' in selection:
            # Individual selection
            selected = []
            for num_str in selection.split(','):
                try:
                    idx = int(num_str.strip())
                    if 1 <= idx <= len(dorks):
                        selected.append(dorks[idx-1])
                except ValueError:
                    print(f"❌ Número inválido: {num_str.strip()}")
            return selected
        else:
            # Single selection
            try:
                idx = int(selection)
                if 1 <= idx <= len(dorks):
                    return [dorks[idx-1]]
                else:
                    print("❌ Número fuera de límites.")
                    return []
            except ValueError:
                print("❌ Selección inválida.")
                return []
    
    def run_selected_dorks(self, selected_dorks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Execute selected dorks and return results"""
        if not selected_dorks:
            print("❌ No se seleccionaron dorks para ejecutar.")
            return {}
        
        print(f"\n🔍 Ejecutando {len(selected_dorks)} dork(s) seleccionado(s)")
        print("=" * 60)
        
        all_results = []
        results_by_dork = {}
        
        for idx, dork in enumerate(selected_dorks, 1):
            dork_id = dork.get('id', 'unknown')
            title = dork.get('title', dork_id)
            
            print(f"\n{idx}. Ejecutando: {title}")
            print("-" * 40)
            
            try:
                results = self.dork_engine.run_dork(dork, num=10, verbose=True)
                results_by_dork[dork_id] = {
                    'dork': dork,
                    'results': results,
                    'count': len(results)
                }
                all_results.extend(results)
                print(f"   ✅ {len(results)} resultados encontrados")
                
            except Exception as e:
                print(f"   ❌ Error: {e}")
                results_by_dork[dork_id] = {
                    'dork': dork,
                    'results': [],
                    'count': 0,
                    'error': str(e)
                }
        
        # Cache results for pagination
        self.results_cache = {
            'all_results': self.dork_engine.deduplicate_results(all_results),
            'results_by_dork': results_by_dork,
            'selected_dorks': selected_dorks
        }
        self.current_page = 1
        
        return {
            'all_results': self.dork_engine.deduplicate_results(all_results),
            'results_by_dork': results_by_dork,
            'total_found': len(all_results),
            'unique_found': len(self.dork_engine.deduplicate_results(all_results))
        }
    
    def show_results_with_pagination(self, results_data: Dict[str, Any]) -> bool:
        """Display results with pagination and navigation options"""
        all_results = results_data.get('all_results', [])
        results_by_dork = results_data.get('results_by_dork', {})
        
        if not all_results:
            print("\n❌ No se encontraron resultados.")
            return True
        
        total_results = len(all_results)
        total_pages = (total_results + self.results_per_page - 1) // self.results_per_page
        
        while True:
            # Calculate page range
            start_idx = (self.current_page - 1) * self.results_per_page
            end_idx = min(start_idx + self.results_per_page, total_results)
            page_results = all_results[start_idx:end_idx]
            
            print(f"\n📊 Resultados de Dorks Interactivos")
            print("=" * 80)
            print(f"Página {self.current_page} de {total_pages} | Total: {total_results} resultados únicos")
            print("-" * 80)
            
            # Show results for current page
            for idx, result in enumerate(page_results, start_idx + 1):
                title = result.get('title', 'Sin título')
                link = result.get('link', 'N/A')
                snippet = result.get('snippet', 'Sin descripción')[:100] + "..." if len(result.get('snippet', '')) > 100 else result.get('snippet', 'Sin descripción')
                quality_score = result.get('quality_score', 0.0)
                
                print(f"\n{idx}. {title}")
                print(f"   URL: {link}")
                print(f"   Calidad: {quality_score:.2f} | Snippet: {snippet}")
            
            # Show pagination controls
            print(f"\n📄 Navegación (Página {self.current_page}/{total_pages}):")
            nav_options = []
            if self.current_page > 1:
                nav_options.append("p) Página anterior")
            if self.current_page < total_pages:
                nav_options.append("n) Página siguiente")
            nav_options.extend([
                "j) Ir a página específica",
                "r) Ver resultados por dork",
                "s) Guardar resultados",
                "f) Filtrar resultados",
                "c) Continuar"
            ])
            
            for option in nav_options:
                print(f"   {option}")
            
            choice = input("\nSelecciona una opción: ").strip().lower()
            
            if choice == 'p' and self.current_page > 1:
                self.current_page -= 1
                continue
            elif choice == 'n' and self.current_page < total_pages:
                self.current_page += 1
                continue
            elif choice == 'j':
                try:
                    target_page = int(input("Número de página: ").strip())
                    if 1 <= target_page <= total_pages:
                        self.current_page = target_page
                        continue
                    else:
                        print("❌ Número de página fuera de rango.")
                except ValueError:
                    print("❌ Introduce un número válido.")
            elif choice == 'r':
                self._show_results_by_dork(results_by_dork)
                continue
            elif choice == 's':
                self._save_results(results_data)
                continue
            elif choice == 'f':
                filtered_results = self._filter_results(all_results)
                if filtered_results:
                    results_data['all_results'] = filtered_results
                    self.current_page = 1
                    print(f"✅ Filtrado completado. {len(filtered_results)} resultados.")
                continue
            elif choice == 'c':
                return True
            else:
                print("❌ Opción inválida.")
    
    def _show_results_by_dork(self, results_by_dork: Dict[str, Any]):
        """Show results organized by dork"""
        print("\n📊 Resultados por Dork")
        print("=" * 50)
        
        for dork_id, dork_data in results_by_dork.items():
            dork = dork_data['dork']
            results = dork_data['results']
            count = dork_data['count']
            title = dork.get('title', dork_id)
            
            print(f"\n🔍 {title} ({dork_id})")
            print(f"   Resultados: {count}")
            
            if results:
                for i, result in enumerate(results[:3], 1):  # Show top 3 per dork
                    link = result.get('link', 'N/A')
                    print(f"   {i}. {link}")
                if count > 3:
                    print(f"   ... y {count - 3} más")
    
    def _save_results(self, results_data: Dict[str, Any]):
        """Save results to JSON file"""
        filename = input("Nombre del archivo (sin extensión): ").strip()
        if not filename:
            filename = "interactive_dork_results"
        
        safe_filename = "".join(c if c.isalnum() or c in ("-", "_") else "_" for c in filename)
        filepath = f"{safe_filename}.json"
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(results_data, f, indent=2, ensure_ascii=False)
            print(f"✅ Resultados guardados en: {filepath}")
        except Exception as e:
            print(f"❌ Error guardando archivo: {e}")
    
    def _filter_results(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filter results based on user criteria"""
        print("\n🔍 Filtros de Resultados")
        print("=" * 30)
        
        keywords = input("Palabras clave (separadas por coma, opcional): ").strip()
        domain_filter = input("Dominio (opcional): ").strip()
        min_quality = input("Calidad mínima (0.0-1.0, opcional): ").strip()
        
        filtered = results
        
        # Filter by keywords
        if keywords:
            keyword_list = [k.strip().lower() for k in keywords.split(',')]
            filtered = [r for r in filtered if any(
                k in r.get('title', '').lower() or 
                k in r.get('snippet', '').lower() 
                for k in keyword_list
            )]
        
        # Filter by domain
        if domain_filter:
            domain_filter = domain_filter.lower()
            filtered = [r for r in filtered if domain_filter in r.get('link', '').lower()]
        
        # Filter by minimum quality
        if min_quality:
            try:
                min_q = float(min_quality)
                filtered = [r for r in filtered if r.get('quality_score', 0.0) >= min_q]
            except ValueError:
                print("⚠️  Calidad mínima inválida, ignorando filtro.")
        
        return filtered
    
    def interactive_camera_mode(self):
        """Enhanced interactive mode for camera dorks"""
        print("\n📹 Modo Cámaras Interactivo")
        print("=" * 50)
        
        camera_dorks = self.catalog.get_by_category('cameras')
        
        # Group by camera type
        axis_dorks = [d for d in camera_dorks if 'axis' in d.get('tags', [])]
        sony_dorks = [d for d in camera_dorks if 'sony' in d.get('tags', [])]
        liveapplet_dorks = [d for d in camera_dorks if 'liveapplet' in d.get('tags', [])]
        other_dorks = [d for d in camera_dorks if d not in axis_dorks and d not in sony_dorks and d not in liveapplet_dorks]
        
        print("Categorías de cámaras disponibles:")
        print("1. AXIS Cameras (AXIS specific dorks)")
        print("2. Sony Cameras (SNC series)")
        print("3. LiveApplet (Java-based cameras)")
        print("4. Otros tipos de cámaras")
        print("5. Todos los dorks de cámaras")
        print("0. Volver")
        
        while True:
            choice = input("\nSelecciona categoría de cámaras (0-5): ").strip()
            
            if choice == '0':
                return
            elif choice == '1':
                selected = self._select_from_group(axis_dorks, "Cámaras AXIS")
            elif choice == '2':
                selected = self._select_from_group(sony_dorks, "Cámaras Sony")
            elif choice == '3':
                selected = self._select_from_group(liveapplet_dorks, "Cámaras LiveApplet")
            elif choice == '4':
                selected = self._select_from_group(other_dorks, "Otros tipos de cámaras")
            elif choice == '5':
                selected = camera_dorks
            else:
                print("❌ Opción inválida.")
                continue
            
            if selected:
                results = self.run_selected_dorks(selected)
                if results:
                    self.show_results_with_pagination(results)
            
            continue_search = input("\n¿Buscar más cámaras? (s/n): ").strip().lower()
            if continue_search not in ['s', 'si', 'y', 'yes']:
                break
    
    def _select_from_group(self, dorks: List[Dict[str, Any]], group_name: str) -> List[Dict[str, Any]]:
        """Helper to select dorks from a group"""
        if not dorks:
            print(f"❌ No hay dorks en la categoría: {group_name}")
            return []
        
        print(f"\n🔍 {group_name} ({len(dorks)} dorks disponibles)")
        
        for idx, dork in enumerate(dorks[:10], 1):  # Show first 10
            title = dork.get('title', 'Sin título')
            query = dork.get('query', '')
            print(f"{idx:2d}. {title}")
            print(f"    Query: {query}")
        
        if len(dorks) > 10:
            print(f"... y {len(dorks) - 10} más")
        
        selection = input(f"\nSelecciona números separados por coma (1-{min(10, len(dorks))}) o 'all': ").strip().lower()
        
        if selection == 'all':
            return dorks
        elif ',' in selection:
            selected = []
            for num_str in selection.split(','):
                try:
                    idx = int(num_str.strip())
                    if 1 <= idx <= min(10, len(dorks)):
                        selected.append(dorks[idx-1])
                except ValueError:
                    pass
            return selected
        else:
            try:
                idx = int(selection)
                if 1 <= idx <= min(10, len(dorks)):
                    return [dorks[idx-1]]
            except ValueError:
                pass
        return []
    
    def interactive_osint_mode(self):
        """Enhanced interactive mode for OSINT dorks"""
        print("\n🔍 Modo OSINT Interactivo")
        print("=" * 50)
        
        osint_dorks = self.catalog.get_by_category('osint')
        
        print("Tipos de OSINT disponibles:")
        print("1. Dominios educativos (.edu)")
        print("2. Documentos públicos (Google Docs)")
        print("3. Subida de archivos")
        print("4. Portales de login")
        print("5. Búsqueda personalizada")
        print("0. Volver")
        
        while True:
            choice = input("\nSelecciona tipo OSINT (0-5): ").strip()
            
            if choice == '0':
                return
            elif choice == '1':
                self._customize_domain_search('.edu', 'Dominios Educativos')
            elif choice == '2':
                self._customize_google_docs_search()
            elif choice == '3':
                self._customize_upload_search()
            elif choice == '4':
                self._customize_login_search()
            elif choice == '5':
                self._custom_generic_osint_search()
            else:
                print("❌ Opción inválida.")
                continue
            
            continue_search = input("\n¿Continuar con OSINT? (s/n): ").strip().lower()
            if continue_search not in ['s', 'si', 'y', 'yes']:
                break
    
    def _customize_domain_search(self, domain_ext: str, category_name: str):
        """Customize domain-based OSINT search"""
        print(f"\n🎯 Búsqueda en {category_name}")
        print("=" * 40)
        
        domain = input(f"Ingresa el dominio base (ej: school, university, etc.): ").strip()
        if not domain:
            return
        
        # Build custom query
        search_types = [
            f"site:{domain}{domain_ext} inurl:login",
            f"site:{domain}{domain_ext} inurl:upload", 
            f"site:{domain}{domain_ext} filetype:pdf",
            f"site:{domain}{domain_ext} \"document\" OR \"confidential\""
        ]
        
        print(f"\nTipos de búsqueda para {domain}{domain_ext}:")
        for idx, query in enumerate(search_types, 1):
            print(f"{idx}. {query}")
        
        selection = input("\nSelecciona números separados por coma o 'all': ").strip().lower()
        
        if selection == 'all':
            selected_queries = search_types
        else:
            selected_queries = []
            for num_str in selection.split(','):
                try:
                    idx = int(num_str.strip())
                    if 1 <= idx <= len(search_types):
                        selected_queries.append(search_types[idx-1])
                except ValueError:
                    pass
        
        if selected_queries:
            self._execute_custom_queries(selected_queries, f"OSINT - {category_name}")
    
    def _customize_google_docs_search(self):
        """Customize Google Docs OSINT search"""
        print(f"\n📄 Búsqueda en Google Docs")
        print("=" * 30)
        
        search_terms = input("Términos de búsqueda (separados por coma): ").strip()
        if not search_terms:
            return
        
        file_types = ["pdf", "doc", "docx", "xls", "xlsx", "ppt", "pptx"]
        print(f"\nTipos de archivo disponibles: {', '.join(file_types)}")
        
        selected_types = input("Selecciona tipos de archivo (separados por coma): ").strip()
        
        if selected_types:
            type_list = [t.strip() for t in selected_types.split(',')]
            selected_types = [t for t in type_list if t in file_types]
        else:
            selected_types = ["pdf"]
        
        queries = []
        for term in search_terms.split(','):
            term = term.strip()
            for file_type in selected_types:
                queries.append(f"site:docs.google.com filetype:{file_type} {term}")
        
        self._execute_custom_queries(queries, "Google Docs OSINT")
    
    def _customize_upload_search(self):
        """Customize file upload OSINT search"""
        print(f"\n📤 Búsqueda de páginas de subida")
        print("=" * 35)
        
        target_domains = input("Dominios objetivo (separados por coma, opcional): ").strip()
        upload_types = ["upload", "files", "attachments", "submit"]
        
        queries = []
        if target_domains:
            for domain in target_domains.split(','):
                domain = domain.strip()
                for upload_type in upload_types:
                    queries.append(f"site:{domain} inurl:{upload_type}")
        else:
            for upload_type in upload_types:
                queries.append(f"inurl:{upload_type} \"upload\" OR \"file\" OR \"attach\"")
        
        self._execute_custom_queries(queries, "Upload Pages OSINT")
    
    def _customize_login_search(self):
        """Customize login portal OSINT search"""
        print(f"\n🔐 Búsqueda de portales de login")
        print("=" * 35)
        
        domain_types = [
            ("Educativos", ".edu"),
            ("Gubernamentales", ".gov"), 
            ("Empresas", ".com"),
            ("Personalizado", "")
        ]
        
        print("Tipos de dominio:")
        for idx, (name, ext) in enumerate(domain_types, 1):
            print(f"{idx}. {name} ({ext if ext else 'custom'})")
        
        choice = input("\nSelecciona tipo (1-4): ").strip()
        
        try:
            choice_idx = int(choice) - 1
            if 0 <= choice_idx < len(domain_types):
                domain_name, domain_ext = domain_types[choice_idx]
                
                if domain_ext:
                    domain = input(f"Subdominio base para {domain_name}: ").strip()
                    if not domain:
                        return
                    base_domain = f"{domain}{domain_ext}"
                else:
                    base_domain = input("Dominio completo: ").strip()
                    if not base_domain:
                        return
                
                queries = [
                    f"site:{base_domain} inurl:login",
                    f"site:{base_domain} inurl:admin",
                    f"site:{base_domain} inurl:signin",
                    f"site:{base_domain} intitle:\"login\" OR intitle:\"sign in\""
                ]
                
                self._execute_custom_queries(queries, f"Login Portals - {domain_name}")
        except ValueError:
            print("❌ Selección inválida.")
    
    def _custom_generic_osint_search(self):
        """Custom generic OSINT search"""
        print(f"\n🔍 Búsqueda OSINT Personalizada")
        print("=" * 35)
        
        custom_query = input("Ingresa tu consulta personalizada: ").strip()
        if not custom_query:
            return
        
        # Add common OSINT operators
        enhanced_queries = [
            custom_query,
            f"{custom_query} filetype:pdf",
            f"{custom_query} site:slideshare.net",
            f"{custom_query} site:scribd.com",
            f"{custom_query} \"contact\" OR \"about\" OR \"team\""
        ]
        
        self._execute_custom_queries(enhanced_queries, "Custom OSINT")
    
    def _execute_custom_queries(self, queries: List[str], search_name: str):
        """Execute custom queries and show results"""
        print(f"\n🚀 Ejecutando {len(queries)} consultas para: {search_name}")
        print("=" * 60)
        
        all_results = []
        
        for idx, query in enumerate(queries, 1):
            print(f"\n{idx}. Ejecutando: {query}")
            try:
                results = self.dork_engine.search_manager.search(query, num=10)
                all_results.extend(results)
                print(f"   ✅ {len(results)} resultados")
            except Exception as e:
                print(f"   ❌ Error: {e}")
        
        # Show results with pagination
        if all_results:
            results_data = {
                'all_results': self.dork_engine.deduplicate_results(all_results),
                'results_by_dork': {},
                'total_found': len(all_results),
                'unique_found': len(self.dork_engine.deduplicate_results(all_results))
            }
            self.show_results_with_pagination(results_data)
        else:
            print("\n❌ No se encontraron resultados.")
    
    def run_interactive_session(self):
        """Main interactive session loop"""
        while True:
            print(f"\n🧨 Dorks Interactivos - Sistema Personalizado")
            print("=" * 60)
            print("Opciones:")
            print("1. Seleccionar dorks por categoría")
            print("2. Modo cámaras interactivo") 
            print("3. Modo OSINT interactivo")
            print("4. Búsqueda personalizada multi-motor")
            print("0. Volver al menú principal")
            
            choice = input("\nSelecciona una opción (0-4): ").strip()
            
            if choice == '0':
                return
            elif choice == '1':
                category = self.show_categories_menu()
                if category:
                    dorks = self.show_dorks_in_category(category)
                    if dorks:
                        selected = self.select_dorks(dorks)
                        if selected:
                            results = self.run_selected_dorks(selected)
                            if results:
                                self.show_results_with_pagination(results)
            elif choice == '2':
                self.interactive_camera_mode()
            elif choice == '3':
                self.interactive_osint_mode()
            elif choice == '4':
                self._custom_multi_engine_search()
            else:
                print("❌ Opción inválida.")
    
    def _custom_multi_engine_search(self):
        """Custom multi-engine search"""
        print(f"\n🔄 Búsqueda Multi-Motor Personalizada")
        print("=" * 50)
        
        query = input("Ingresa tu consulta personalizada: ").strip()
        if not query:
            return
        
        num_results = input("Número de resultados por motor (default: 10): ").strip()
        try:
            num = int(num_results) if num_results else 10
        except ValueError:
            num = 10
        
        try:
            # Use cross-engine comparison
            comparison = self.dork_engine.search_manager.compare_results(query, num)
            
            if comparison:
                print(f"\n🔍 Resultados multi-motor para: {query}")
                print("=" * 60)
                
                results_by_engine = comparison.get('results_by_engine', {})
                for engine_type, results in results_by_engine.items():
                    print(f"\n{engine_type.value.title()}: {len(results)} resultados")
                
                # Show top results
                all_results = []
                for results in results_by_engine.values():
                    all_results.extend(results)
                
                if all_results:
                    # Get best combined results
                    results_list = list(results_by_engine.values())
                    best_results = self.dork_engine.search_manager.comparator.get_best_results(results_list, top_n=20)
                    
                    print(f"\n🏆 Mejores resultados combinados:")
                    for i, result in enumerate(best_results[:10], 1):
                        title = result.get('title', 'Sin título')
                        link = result.get('link', 'N/A')
                        print(f"{i}. {title}")
                        print(f"   URL: {link}")
                
                # Save option
                save = input("\n¿Guardar resultados? (s/n): ").strip().lower()
                if save in ['s', 'si', 'y', 'yes']:
                    filename = input("Nombre del archivo: ").strip() or "multi_engine_results"
                    try:
                        with open(f"{filename}.json", 'w', encoding='utf-8') as f:
                            json.dump(comparison, f, indent=2, ensure_ascii=False)
                        print(f"✅ Guardado en: {filename}.json")
                    except Exception as e:
                        print(f"❌ Error guardando: {e}")
            
        except Exception as e:
            print(f"❌ Error en búsqueda multi-motor: {e}")