# Release Notes v1.0.0

Nos enorgullece anunciar la primera versión estable (v1.0.0) del **Esperanto PDF Repair Engine**.

Esta versión marca el paso de un prototipo analítico a un producto robusto y con capacidades de procesamiento masivo, asegurando siempre el principio de oro: **"No modificar nunca el PDF original"**.

## 🌟 Capacidades Clave

- **Procesamiento Masivo (Batch Processing):** Soporte completo para cargar y procesar colas de múltiples archivos PDF simultáneamente.
- **Pipeline de Reparación Híbrido (Offline):** Orquestación heurística de 7 niveles (Radiko, Morfo, Frekvenco, Kunteksto, Gramatiko, Jugxanto, Restarigo) 100% aislados de internet (Air-Gapped).
- **Inyección Transparente (PyMuPDF):** Las palabras reparadas se reinyectan al PDF de origen creando una capa de texto transparente ("invisible") sobre el texto mal codificado, permitiendo búsquedas y extracción sin desconfigurar la maquetación.
- **Manual Review System:** Interfaz interactiva para moderar falsos positivos y palabras de baja confianza (inferior a 0.85).
- **Exportación de Reportes Globales:** Exportación integrada de datos estadísticos consolidados en formatos CSV y JSON.

## 🏗 Arquitectura Definitiva

El Repair Engine se ejecuta como un servicio dual:
1. **Frontend:** Panel de Control de Next.js.
2. **Backend:** FastAPI, comunicándose vía SQLite local, usando concurrencia asincrónica mediante Tareas en Segundo Plano. Todo esto se articula sin requerir servicios en la Nube.

## 📊 Métricas de Validación

Durante nuestras validaciones QA sobre las 30 lecciones del curso oficial de Esperanto (Fase B):
- **Automatización Alcanzada:** 97.10% (234 de 241 casos de ambigüedad severa resueltos sin intervención humana).
- **Tasa de Recuperación General:** > 99.4%.
- **Prevención de Alucinaciones (Falsos Positivos):** 7 casos se enviaron a validación manual intencionalmente para evitar corrupciones silenciosas, validando un umbral de seguridad estricto del 85%.
- **Mitigación Bilingüe:** El analizador bilingüe evita la sobre-corrección en textos paralelos Español-Esperanto, deduciendo contextos traductológicos directamente en las cercanías de la palabra corrupta.

## ⚠️ Limitaciones y Riesgos Conocidos

- **H-System Complejo:** Los textos que deliberadamente combinan X-System ("cx") con el clásico H-System ("ch") en idiomas no normativos pueden disparar advertencias de baja confianza en el analizador Hunspell.
- **Fuentes Embebidas:** Si el creador original eliminó deliberadamente la tabla CMAP de las fuentes del PDF, el extractor base de PyMuPDF extraerá basura binaria. El script puede repararlo solo parcialmente, dependiendo del nivel de daño en los bloques del archivo.

## 🛠 Decisiones Técnicas Importantes

- **Priorización de Caché Offline:** Se decidió evitar el uso de APIs externas o peticiones directas a Wikipedia durante la ejecución del Batch Processor para proteger la fiabilidad del servicio en entornos corporativos o restringidos.
- **Revisión Segura:** En vez de sobrescribir archivos con correcciones manuales, el sistema genera de forma aditiva `_repaired_reviewed.pdf`, manteniendo toda la trazabilidad.
