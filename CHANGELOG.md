# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-06-09

### Added
- **Batch Processing Dashboard**: Nueva interfaz unificada en el frontend (Next.js) para gestionar documentos y observar progreso.
- **Flujo de Descargas**: Rutas directas para descargar `_repaired.pdf` y `_repaired_reviewed.pdf` desde la UI.
- **Exportación Global**: Exportación local en CSV y JSON consolidada.
- **Frequency Ranking Cache**: Sistema offline para desempatar ambigüedades morfológicas basado en frecuencias pre-cacheadas, evitando latencia HTTP y fallos de conexión.
- **PyMuPDF Inyección**: Inyección de texto por medio de transparencia OCR, preservando el PDF inmutable original.

### Changed
- Reestructuración de la base de datos (SQLite) para integrar columnas analíticas (updated_at) y registro de decisiones de QA.
- El panel técnico "Request Debug" migrado a un dashboard humano denominado "Estado de Auditoría y Reparación".

### Fixed
- Corregida lógica cruzada entre H-System y X-System durante transliteraciones Hunspell que creaban sobrecorrecciones en palabras no esperantizadas.

## [0.5.0] - 2026-05-15

### Added
- Pipeline de 5 Capas activado: Dictionary, X-System, Glyph, Morphological y Hunspell Recovery.
- Soporte base en Backend (FastAPI).
- Interfaz gráfica MVP.

### Fixed
- Soporte inicial para archivos PDF dañados que combinaban glifos incorrectos (ej: `felic^a` o caracteres rusos).

## [0.1.0] - 2026-04-01

### Added
- Prueba de concepto (PoC) y extracción en crudo usando `PyMuPDF`.
- Módulo de auditoría básica para identificar problemas de fuentes (cmap).
- Arquitectura inicial de repositorios en local.
