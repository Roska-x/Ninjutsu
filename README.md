# 🔍 Kit Avanzado de Descubrimiento de Credenciales

Herramienta potente y completa de evaluación de seguridad para descubrir credenciales expuestas, archivos sensibles y vulnerabilidades de seguridad utilizando técnicas avanzadas de Google Dorking y múltiples métodos de descubrimiento.

## 🚀 Características

### Capacidades principales
- **Dorking multi-motor (Google + DuckDuckGo)**: consultas avanzadas optimizadas por motor para encontrar archivos sensibles
- **Interfaz de búsqueda unificada**: capa común sobre distintos motores (`SearchEngineInterface`) con normalización de resultados
- **Búsqueda en GitHub**: búsquedas especializadas de credenciales expuestas en GitHub
- **Descubrimiento de subdominios**: enumeración de subdominios usando DNS, motores de búsqueda y transparencia de certificados
- **Descubrimiento de endpoints de API**: encontrar endpoints de API expuestos y documentación
- **Búsqueda avanzada de dorks desde catálogo JSON**: ejecución masiva de dorks por categoría, con resultados combinados y deduplicados
- **Generación automática de reportes**: generación de reportes completos en HTML, texto y JSON
- **Evaluación de riesgo**: puntuación e identificación inteligente de nivel de riesgo por hallazgo (incluye `quality_score` y `risk_score`)
- **Asistente LLM con Groq**: generación inteligente de dorks a partir de lenguaje natural y análisis de consultas existentes

### Descubrimiento de objetivos
- ✅ Archivos `.env` con credenciales
- ✅ Archivos de configuración (config.js, settings.json, etc.)
- ✅ Cadenas de conexión a bases de datos
- ✅ Claves y secretos de API
- ✅ Configuraciones de servicios en la nube (AWS, Azure, GCP)
- ✅ Tokens y sesiones de autenticación
- ✅ Claves privadas y certificados
- ✅ Paneles de administración y páginas de login

## 📁 Estructura de archivos

```
📁 credential-discovery-toolkit/
├── 📄 master_tool.py              # Interfaz principal unificada (menú maestro multi-motor)
├── 📄 credential_finder.py        # Motor principal de descubrimiento de credenciales (single y cross-engine)
├── 📄 subdomain_finder.py         # Herramienta de enumeración de subdominios
├── 📄 report_generator.py         # Generador automático de reportes
├── 📄 google_dorking_templates.py # Consultas de búsqueda preconstruidas
├── 📄 dork_catalog.py             # Carga y consulta el catálogo de dorks (dorks_catalog.json)
├── 📄 dork_engine.py              # Motor de ejecución de dorks (incluye búsqueda de libros PDF y cross-engine)
├── 📄 dorks_catalog.json          # Catálogo JSON de dorks avanzados (incluye categoría pdf_books)
├── 📄 search_engine_interface.py  # Interfaz unificada y gestor multi-motor (Google, DuckDuckGo, etc.)
├── 📄 googlesearch.py             # Implementación del motor Google Custom Search
├── 📄 duckduckgo_serpapi.py       # Implementación del motor DuckDuckGo vía SerpAPI (web, imágenes, news, trending)
├── 📄 query_optimizer.py          # Optimizador de queries por motor + EngineAwareSearchManager
├── 📄 ninjadorks.py               # Script de dorking LEGADO / DEPRECATED (no se usa en los nuevos flujos)
├── 📄 llm_dork_assistant.py       # Asistente LLM basado en Groq para generación y análisis de dorks
├── 📄 requirements.txt            # Dependencias de Python
├── 📄 .env                        # Archivo de configuración
└── 📄 README.md                   # Esta documentación
```

## 🛠️ Instalación

### Prerrequisitos
- Python 3.6 o superior
- Claves de API para los motores de búsqueda (Google Custom Search opcional, SerpAPI, Serper, Groq)
- Conexión a Internet

### Instrucciones de configuración

1. **Clonar o descargar el kit**
   ```bash
   # No hay repositorio git, solo copia los archivos
   ```

2. **Instalar dependencias**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configurar las APIs necesarias**
    - **API de Google Custom Search** (opcional, pero recomendado para búsquedas avanzadas):
      - Crea un Google Custom Search Engine en [Google CSE](https://cse.google.com)
      - Obtén tu clave de API y tu Search Engine ID
    - **API de SerpAPI** (para búsquedas en DuckDuckGo):
      - Regístrate en [SerpAPI](https://serpapi.com/)
      - Obtén tu clave de API
    - **API de Serper** (para búsquedas en Google vía Serper):
      - Regístrate en [Serper](https://serper.dev/)
      - Obtén tu clave de API
    - **API de Groq** (para el asistente LLM):
      - Regístrate en [Groq](https://groq.com/)
      - Obtén tu clave de API
    - Actualiza el archivo `.env` con todas las claves necesarias:
      ```env
      # API de Google Custom Search (opcional)
      API_KEY_GOOGLE=your_google_api_key_here
      SEARCH_ENGINE_ID=your_search_engine_id_here

      # API de SerpAPI para DuckDuckGo
      SERP_API_KEY=your_serpapi_key_here

      # API de Serper para Google
      SERPER_API_KEY=your_serper_api_key_here

      # API de Groq para LLM
      GROQ_API_KEY=your_groq_api_key_here

      # Opcional: segundos de espera entre llamadas a la API de Google
      GOOGLE_SLEEP_SECONDS=1.0
      ```

## 🎯 Inicio rápido

### Opción 1: Herramienta maestra (recomendado)
Ejecuta la interfaz unificada que combina todas las herramientas:
```bash
python master_tool.py
```

### Opción 2: Herramientas individuales
```bash
# Solo descubrimiento de credenciales
python credential_finder.py

# Enumeración de subdominios
python subdomain_finder.py

# Generar reportes desde archivos JSON
python report_generator.py

# Ver plantillas de dorking
python google_dorking_templates.py

# Asistente LLM de dorks
python llm_dork_assistant.py
```

## 📖 Guía de uso

### Interfaz de la herramienta maestra
La herramienta maestra proporciona un menú amigable con las siguientes opciones (las mismas que verás en `master_tool.py`):

1. **🔍 Buscador de credenciales (interactivo)**
   - Búsqueda interactiva de credenciales con múltiples categorías de búsqueda
   - Visualización de resultados en tiempo real
   - Guardar hallazgos en archivos JSON

2. **🌐 Descubrimiento de subdominios**
   - Fuerza bruta de DNS
   - Enumeración mediante búsqueda en Google
   - Búsquedas en logs de transparencia de certificados
   - Escaneo de puertos de los subdominios descubiertos

3. **📊 Plantillas de Google Dorking**
   - Consultas de búsqueda preconstruidas para distintos objetivos
   - Organizadas por categoría (archivos env, archivos de configuración, claves de API, etc.)
   - Personalizables para dominios específicos

4. **🧨 Dorks avanzados multi-motor (Google + DuckDuckGo)**
   - Ejecuta dorks avanzados definidos en el catálogo JSON
   - Permite elegir categorías (credenciales, backups, cámaras, logs, osint, pdf_books, etc.)
   - Muestra los resultados y permite guardarlos en archivos JSON

5. **📚 Búsqueda de libros PDF**
   - Búsqueda avanzada de libros y recursos en PDF usando Google Dorking
   - Permite filtrar por título, autor, tema y pistas de idioma (es/en)
   - Guarda los resultados en archivos JSON para análisis posterior

6. **🔄 Búsqueda cruzada entre motores**
   - Búsqueda de credenciales, configuraciones y endpoints de API usando múltiples motores
   - Comparación de resultados entre Google y DuckDuckGo
   - Filtros avanzados para refinar hallazgos

7. **📈 Generar reportes**
   - Crear reportes detallados a partir de datos JSON
   - Múltiples formatos de salida (HTML, texto, JSON)
   - Evaluación y categorización de riesgo

8. **🚀 Escaneo rápido (todas las herramientas)**
   - Escaneo de seguridad completo de un dominio
   - Combina descubrimiento de subdominios, búsqueda de credenciales y generación de reportes

9. **⚙️ Configuración motores**
   - Configuración global del motor de búsqueda (Google, DuckDuckGo, auto-select)
   - Pruebas de configuración y consejos de optimización

10. **📊 Comparación de rendimiento**
    - Comparación de rendimiento entre motores de búsqueda
    - Análisis de calidad y solapamiento de resultados

11. **📚 Ayuda y documentación**
    - Muestra un resumen de uso y buenas prácticas
    - Incluye recordatorios legales y de uso responsable

12. **🖼️ Búsquedas avanzadas (imágenes / noticias / trending)**
    - Búsqueda de imágenes, noticias y tendencias usando DuckDuckGo
    - Funcionalidades avanzadas del motor de búsqueda

13. **🧨 Dorks interactivos (selección personalizada)**
    - Sistema interactivo para selección y ejecución de dorks personalizados
    - Navegación paginada y opciones de personalización

14. **📹 Modo cámaras (dorks personalizados)**
    - Dorks especializados para búsqueda de cámaras IP y sistemas de vigilancia
    - Plantillas preconstruidas y ejecución personalizada

15. **🔑 Búsqueda de API Keys (todas las plataformas)**
    - Búsqueda específica de claves de API de múltiples plataformas (OpenAI, GitHub, Slack, Google, etc.)
    - Soporte para búsqueda multi-motor y personalizada

16. **🤖 Asistente LLM de dorks (Groq)**
    - Asistente inteligente basado en Groq para generar y analizar dorks
    - Genera dorks a partir de descripciones en lenguaje natural
    - Explica qué hace un dork y su nivel de riesgo
    - Sugiere dorks relacionados y variantes

17. **🔎 SmartSearch sobre resultados locales**
    - Búsqueda avanzada con expresiones regulares sobre archivos de resultados locales
    - Análisis forense de datos guardados anteriormente

18. **❌ Salir**
     - Cierra la herramienta de forma segura

### Asistente LLM de Dorks

El asistente LLM integrado utiliza la API de Groq para proporcionar funcionalidades avanzadas de generación y análisis de dorks:

#### Funcionalidades principales:
- **Generación de dorks**: Convierte descripciones en lenguaje natural en consultas de Google Dorking optimizadas
- **Análisis de dorks**: Explica qué hace una consulta específica y qué tipo de resultados puede encontrar
- **Sugerencias relacionadas**: Propone variantes y dorks complementarios a partir de una consulta base
- **Optimización por motor**: Adapta las consultas para Google o DuckDuckGo según sea necesario

#### Ejemplos de uso:
```bash
# Generar dorks para encontrar archivos de configuración expuestos
"archivos de configuración con contraseñas en GitHub"

# Analizar un dork existente
site:github.com "password" filetype:env

# Obtener variantes de un dork
site:github.com ".env" "DB_PASSWORD"
```

El asistente está disponible tanto desde el menú principal (opción 17) como ejecutando directamente `python llm_dork_assistant.py`.

### Opciones del buscador de credenciales

El buscador de credenciales incluye búsquedas especializadas para:

#### Archivos .env
- Archivos .env genéricos
- Archivos con contraseñas de base de datos
- Claves y secretos de API
- Configuraciones de servicios en la nube

#### Archivos de configuración
- config.js con credenciales
- settings.json con claves de API
- webpack.config.js con variables de entorno
- Archivos de configuración PHP y YAML

#### Credenciales
- Contraseñas de bases de datos (MySQL, PostgreSQL, MongoDB)
- Credenciales de administrador
- Claves privadas y certificados
- Claves de acceso de AWS, Azure, GCP

#### Endpoints de API
- Endpoints REST API
- Endpoints GraphQL
- Documentación Swagger
- Colecciones de Postman

### Categorías de Google Dorking

El kit incluye consultas preconstruidas para:

1. **Archivos de entorno**
   ```
   site:github.com ".env" filetype:env
   inurl:.env "password" OR "db_password"
   ```

2. **Archivos de configuración**
   ```
   site:github.com "config.js" "password" OR "api_key"
   site:github.com "settings.json" "secret" OR "token"
   ```

3. **Claves de API**
   ```
   "AIzaSy" API_KEY (Google APIs)
   "sk_live_" stripe key
   "AKIA" AWS access key
   ```

4. **Configuraciones de base de datos**
   ```
   site:github.com "database.yml" "password"
   site:github.com "mongoose.js" "password"
   ```

5. **Servicios en la nube**
   ```
   site:github.com "aws_access_key_id"
   site:github.com "azure" "connection_string"
   site:github.com "firebase" "config"
   ```

### Dorks avanzados (catálogo)

Además de las plantillas básicas, el proyecto incluye un catálogo de dorks avanzados definido en el archivo `dorks_catalog.json` y ejecutado por `dork_engine.py` (usado desde el menú de dorks avanzados en `master_tool.py`).

Cada entrada del catálogo contiene:
- `id`: identificador único del dork
- `category`: categoría (por ejemplo: `credentials`, `env_files`, `cloud_configs`, `backup_files`, `logs`, `login_panels`, `cameras`, `index_of`, `osint`, `pdf_books`, etc.)
- `title`: descripción legible del dork
- `query`: consulta de Google Dorking
- `risk`: nivel de riesgo estimado (`high`, `medium`, `low`, `info`)
- `tags`: etiquetas útiles para clasificar y buscar dorks

Desde el menú **🧨 Dorks avanzados multi-motor (Google + DuckDuckGo)** puedes:
- Listar las categorías disponibles del catálogo
- Ejecutar todos los dorks de una categoría
- Ver los resultados en pantalla
- Guardar los resultados combinados en un archivo JSON

### Búsqueda de libros y PDFs

La opción **📚 Búsqueda de libros PDF** del menú principal utiliza la categoría `pdf_books` del catálogo de dorks para localizar libros y recursos en PDF en Internet.

Características principales:
- Usa como mínimo el **título** del libro (`title`) como parámetro obligatorio.
- Permite agregar:
  - **Autor** (`author`)
  - **Tema** o **materia** (`topic`, por ejemplo: hacking, redes, OSINT)
  - **Idioma** (`lang`, por ejemplo: `es` o `en`) para priorizar dorks con pistas de idioma.
- Ejecuta múltiples dorks especializados, como:
  - Búsqueda por título exacto
  - Título + autor
  - Título + tema
  - Resultados en universidades (`.edu`, `.ac.*`)
  - Resultados en Google Drive/Docs
  - "index of" con PDFs
- Todos los dorks de la categoría `pdf_books` se combinan, se eliminan duplicados y se muestran de forma unificada.

El flujo típico es:
1. Ingresar **título** (obligatorio), **autor**, **tema** y/o **idioma** (opcionales).
2. Ver los resultados de Google (solo se muestran metadatos y URLs, no se descargan archivos automáticamente).
3. Guardar los resultados en un archivo JSON para revisarlos o procesarlos después (por ejemplo, `pdf_books_<titulo_sanitizado>.json`).

## 🔧 Funciones avanzadas

### Evaluación de riesgo
El kit clasifica automáticamente los hallazgos por nivel de riesgo:
- **ALTO**: contraseñas, claves privadas, tokens de API
- **MEDIO**: archivos de configuración, paneles de administración
- **BAJO**: endpoints públicos, documentación
- **INFO**: exposición de información general

Además, en los resultados verás dos métricas numéricas:

- `quality_score`: mide la calidad del resultado (snippet presente, título razonable, HTTPS, dominio "reputable", etc.).
- `risk_score`: mide de forma **heurística** cuán sensible parece el resultado (0.00–1.00).

`risk_score` se calcula en [`CredentialFinder._compute_risk_score()`](credential_finder.py:409) combinando:

1. **Tipo de fichero sensible**
   Si la URL parece apuntar a `.env`, `.config`, `.yml`, `.php`, `.json`, etc., suma riesgo.

2. **Palabras clave de credenciales**
   Si en el título/snippet aparecen términos como `password`, `secret`, `token`, `api_key`, `access_key`, `private key`, etc., suma riesgo.

3. **Dominio**
   Resultados fuera de GitHub/GitLab se consideran ligeramente más riesgosos (es más probable que sean leaks "reales" en sitios de producción).

> 📌 Importante: cuando usas la búsqueda de **libros PDF**, `risk_score` sigue mostrando esta heurística general, pero:
> - No está pensado para evaluar ilegalidad o copyright de los libros.
> - Normalmente será bajo o medio, porque los PDFs no suelen coincidir con los patrones de credenciales.
> - Úsalo solo como indicador técnico de "parece fichero sensible de config/credenciales", no como medida legal o ética sobre el contenido del libro.

### Generación de reportes
Hay disponibles múltiples formatos de reporte:

1. **Reportes HTML**
   - Estilo interactivo y profesional
   - Categorización de riesgo con código de colores
   - Enlaces clicables y metadatos
   - Estadísticas y gráficos de resumen

2. **Reportes de texto**
   - Texto plano para lectura sencilla
   - Adecuado para revisión en línea de comandos
   - Disposición estructurada de la información

3. **Reportes JSON**
   - Formato legible por máquinas
   - Datos estructurados para integración
   - Metadatos completos
   - Adecuados para pipelines de CI/CD

### Métodos de descubrimiento de subdominios

1. **Fuerza bruta de DNS**
   - Wordlist de subdominios comunes
   - Resolución multi-hilo
   - Más de 50 subdominios probados simultáneamente

2. **Búsqueda en Google**
   - Consultas `site:*.domain.com`
   - Análisis de patrones de URL
   - Extracción de subdominios desde los resultados

3. **Transparencia de certificados**
   - Integración con la API de crt.sh
   - Datos históricos de certificados
   - Soporte para dominios wildcard

4. **Escaneo de puertos**
   - Enumeración de servicios
   - Puertos comunes (22, 23, 53, 80, 135, 139, 443, 993, 995)
   - Escaneo concurrente con ThreadPoolExecutor

## 📊 Ejemplo de salida

### Resultados de un escaneo rápido
```
🚀 Iniciando escaneo rápido de seguridad para: example.com
===========================================================

🔍 Paso 1: Descubriendo subdominios...
  ✅ Encontrado: www.example.com
  ✅ Encontrado: mail.example.com
  ✅ Encontrado: api.example.com
  ✅ Encontrado: admin.example.com

🔍 Paso 2: Descubrimiento de credenciales...
  ✅ 15 resultados relacionados con credenciales encontrados

🔍 Paso 3: Generando resumen del escaneo...
  ✅ ¡Reportes generados correctamente!

===========================================================
🎯 RESUMEN DE ESCANEO RÁPIDO - example.com
===========================================================
📊 Total de subdominios encontrados: 12
🔑 Hallazgos de credenciales: 15
🚨 Nivel de riesgo: ALTO
⏰ Hora del escaneo: 2025-11-20 17:45:02
===========================================================

⚠️  ADVERTENCIA: ¡Se detectaron posibles problemas de seguridad!
📁 Revisa los reportes generados para ver los hallazgos en detalle.
```

## 🛡️ Consideraciones de seguridad

### Aviso legal
⚠️ **IMPORTANTE**: Esta herramienta está diseñada para profesionales de seguridad y SOLO debe usarse en:
- Sistemas que te pertenezcan
- Sistemas para los cuales tengas permiso explícito y por escrito para realizar pruebas
- Proyectos de pentesting autorizados

### Uso responsable
- Sigue prácticas de divulgación responsable
- Respeta los límites de velocidad y recursos de los servidores
- No intentes explotar las vulnerabilidades encontradas
- Reporta los problemas de seguridad por los canales adecuados

### Limitación de velocidad (Rate limiting)
El kit incluye limitación de velocidad incorporada para:
- Respetar las cuotas de la API de Google
- Evitar sobrecargar los servidores objetivo
- Mantener prácticas de escaneo éticas

## 🔧 Configuración

### Variables de entorno
```env
# API de Google Custom Search (opcional)
API_KEY_GOOGLE=your_google_api_key
SEARCH_ENGINE_ID=your_search_engine_id

# API de SerpAPI para DuckDuckGo
SERP_API_KEY=your_serpapi_key

# API de Serper para Google
SERPER_API_KEY=your_serper_api_key

# API de Groq para LLM
GROQ_API_KEY=your_groq_api_key

# Opcional: segundos de espera entre llamadas a la API de Google
GOOGLE_SLEEP_SECONDS=1.0
```

- `API_KEY_GOOGLE`: clave de la API de Google Custom Search (opcional, pero recomendado).
- `SEARCH_ENGINE_ID`: identificador del motor de búsqueda personalizado de Google (CSE).
- `SERP_API_KEY`: clave de API de SerpAPI para búsquedas en DuckDuckGo.
- `SERPER_API_KEY`: clave de API de Serper para búsquedas en Google.
- `GROQ_API_KEY`: clave de API de Groq para el asistente LLM.
- `GOOGLE_SLEEP_SECONDS`: (opcional) pausa en segundos entre consultas a la API de Google para respetar el rate limiting (valor por defecto: `1.0`).

### Opciones de personalización

1. **Wordlists**: modifica las wordlists de subdominios en `subdomain_finder.py`
2. **Consultas de búsqueda**: añade consultas de dorking personalizadas en `google_dorking_templates.py`
3. **Lista de puertos**: personaliza el escaneo de puertos en el buscador de subdominios
4. **Patrones de riesgo**: modifica los patrones de evaluación de riesgo en `report_generator.py`
5. **Catálogo de dorks avanzados**: edita `dorks_catalog.json` para añadir, ajustar o desactivar dorks avanzados (incluida la categoría `pdf_books` para búsqueda de libros y recursos en PDF)

## 📈 Rendimiento

### Funciones de optimización
- **Procesamiento concurrente**: ThreadPoolExecutor para operaciones en paralelo
- **Limitación de velocidad**: demoras integradas para respetar los límites de la API
- **Manejo de errores**: gestión robusta de errores y lógica de reintentos
- **Eficiente en memoria**: procesamiento en streaming para conjuntos de resultados grandes

### Escalabilidad
- Puede procesar cientos de subdominios de forma simultánea
- Maneja eficientemente conjuntos de resultados grandes
- Adecuado para evaluaciones de seguridad a nivel empresarial

## 🚨 Solución de problemas

### Problemas comunes

1. **"No se encontraron resultados"**
   - Verifica la configuración de la API de Google
   - Verifica la conexión a Internet
   - Asegúrate de que el motor de búsqueda esté configurado correctamente

2. **"Error al realizar la solicitud"**
   - Verifica la validez de la clave de API
   - Verifica el Search Engine ID
   - Comprueba las cuotas y límites de la API

3. **Errores de importación de módulos**
   ```bash
   pip install -r requirements.txt
   ```

4. **Problemas de resolución DNS**
   - Verifica la conexión a Internet
   - Verifica la configuración de DNS
   - Algunos entornos pueden bloquear consultas DNS

### Modo de depuración
Añade prints de depuración para ver información detallada de errores:
```python
# En cualquier herramienta, añade:
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 📚 Recursos adicionales

### Referencias de Google Dorking
- [Operadores de búsqueda avanzada de Google](https://support.google.com/websearch/answer/2466433)
- [Base de datos de Google Dorking](https://www.exploit-db.com/google-hacking-database)

### Mejores prácticas de seguridad
- [Guía de pruebas OWASP](https://owasp.org/www-project-web-security-testing-guide/)
- [Marco de ciberseguridad NIST](https://www.nist.gov/cyberframework)

## 🤝 Contribuciones

Este kit está diseñado para ser extensible. Para añadir nuevas funcionalidades:

1. **Nuevas categorías de búsqueda**: añade consultas a `google_dorking_templates.py`
2. **Herramientas adicionales**: crea nuevos módulos siguiendo los patrones existentes
3. **Formatos de reporte**: amplía `report_generator.py` con nuevos formatos
4. **Evaluación de riesgo**: mejora los algoritmos de categorización de riesgo

## 📄 Licencia

Esta herramienta se proporciona con fines educativos y de pruebas de seguridad autorizadas únicamente. Los usuarios son responsables de cumplir con todas las leyes y regulaciones aplicables.

## ⚠️ Descargo de responsabilidad

Los autores no son responsables del uso indebido de esta herramienta. Está pensada para:
- Profesionales de seguridad
- Pentesters
- Investigadores de seguridad
- Administradores de sistemas (para sus propios sistemas)

**Úsala de forma responsable y ética.**

---

## 📞 Soporte

Para problemas, preguntas o contribuciones:
- Revisa esta documentación detenidamente
- Consulta la sección de solución de problemas
- Asegúrate de que la configuración sea correcta
- Verifica que todas las dependencias estén instaladas

**Recuerda**: esta es una herramienta de seguridad potente; úsala con sabiduría y responsabilidad. 🔒
