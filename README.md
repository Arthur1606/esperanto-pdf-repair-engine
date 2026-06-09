# Esperanto PDF Repair Engine

Un sistema avanzado y **100% offline (air-gapped)** diseñado para reparar PDFs de Esperanto que sufren de corrupción en la codificación de caracteres.

## 📖 Descripción

### El Problema
Al generar, imprimir o exportar documentos PDF antiguos (especialmente materiales educativos de Esperanto), los caracteres especiales con circunflejo (ĉ, ĝ, ĥ, ĵ, ŝ, ŭ) suelen perder su codificación. Estos son reemplazados por glifos corruptos, caracteres de otros idiomas (ej. cirílico), o transliteraciones híbridas del X-System o H-System. Esto no solo afecta la legibilidad para el usuario, sino que destruye la indexación y la capacidad de búsqueda (Copy & Paste / CTRL+F) del texto dentro del PDF.

### Motivación del Proyecto
La preservación histórica de textos en Esperanto requiere herramientas de recuperación semántica. El *Repair Engine* nace con el objetivo de restaurar de forma masiva bibliotecas digitales sin comprometer la privacidad de los documentos, funcionando sin dependencias a servicios en la nube ni APIs pagas.

## ✨ Características

- **Auditoría Automática:** Escaneo veloz de fuentes incrustadas (CMAP) y conteo de caracteres dañados.
- **Reparación Unicode:** Restauración morfológica profunda que arregla palabras declinadas, plurales o transliteradas de forma mixta.
- **Procesamiento Masivo:** Carga y reparación en lote de decenas de documentos PDF en paralelo.
- **Revisión Manual:** Interfaz interactiva para revisar y aprobar/rechazar las decisiones automatizadas de baja confianza (falsos positivos).
- **Funcionamiento Offline:** Motor aislado, utilizando cachés de frecuencia locales y diccionarios Hunspell nativos.

## 🚀 Tecnologías

**Backend:**
- **Python** (Core Pipeline)
- **FastAPI** (Servicios RESTful y Background Tasks)
- **SQLite** (Persistencia transaccional)
- **PyMuPDF** (Lectura, Extracción e Inyección de Capas de Texto)
- **Spylls / Hunspell** (Motor ortográfico local)

**Frontend:**
- **Next.js** (Framework React)
- **TypeScript** (Tipado seguro)
- **Tailwind CSS** (Interfaz visual moderna y responsive)

## 🏗 Arquitectura

### How It Works
El sistema procesa los documentos defectuosos a través de un esquema en cascada heurístico (6 Capas) antes de reinyectarlos en el PDF:

       [ PDF Original Corrupto ]
                  ↓
         [ Text Extraction ]
         (PyMuPDF / Font Audit)
                  ↓
          [ Deku Layer ]
       (Dictionary Exact Match)
                  ↓
         [ Sheikah Layer ]
     (Morphological & Hunspell)
                  ↓
          [ Nayru Layer ]
       (Unigram Frequency)
                  ↓
         [ Ocarina Layer ]
(Contextual N-grams, 14MB Corpus)
                  ↓
          [ Farore Layer ]
     (Grammar & Bilingual Rules)
                  ↓
         [ Triforce Layer ]
   (Final Resolution & Confidence)
                  ↓
          [ Master Layer ]
   (Invisible Text Injection)
                  ↓
         [ PDF Restaurado ]
```

### Resultados Finales (Fase B)
- **Volumen de Prueba:** 30 lecciones reales.
- **Automatización:** 97.10% (234 casos resueltos automáticamente).
- **Seguridad:** 7 casos protegidos por el umbral de seguridad estricto (0.85) enviados a revisión manual.
- **Naturaleza del Pipeline:** 0% IA Generativa, 0% APIs externas, 100% Offline y Determinista.

## 📦 Instalación

### Backend
El backend requiere Python 3.9 o superior.

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Frontend
El frontend requiere Node.js v18+.

```bash
cd frontend
npm install
```

## 🖥️ Ejecución Local

1. **Levantar la API (Backend):**
   ```bash
   cd backend
   source venv/bin/activate
   uvicorn main:app --host 127.0.0.1 --port 8000
   ```
2. **Levantar la Interfaz (Frontend):**
   ```bash
   cd frontend
   npm run dev
   ```
   *Accede a [http://localhost:3000](http://localhost:3000)*.

## 🕹️ Flujo de Uso

1. **Subir PDF:** Carga tu(s) documento(s) en la interfaz inicial.
2. **Auditar:** Observa el estado en la tabla de la interfaz mientras el servidor extrae la metadata y la calidad del texto.
3. **Revisar sugerencias:** Detecta visualmente en la tabla si hay advertencias (warnings) de baja confianza.
4. **Ejecutar reparación:** El PDF pasará por el pipeline de inyección, incrustando los metadatos y fuentes requeridas (`NotoSans-Regular.ttf`).
5. **Descargar PDF reparado:** En la tabla, haz clic en el botón `[↓ Auto]` para descargar la versión corregida.
6. **Resolver casos manuales:** Dirígete a la ventana de *Manual Review* para aprobar correcciones de baja confianza y presiona `[↓ Review]` para descargar la versión homologada por humanos.

## ⚠️ Limitaciones Conocidas

- Falsos positivos mínimos cuando el PDF mezcla deliberadamente grandes bloques de texto en español y Esperanto (el detector de idioma lo mitiga, pero no es infalible).
- La reinyección de fuentes no puede recrear formas vectoriales (glifos) de fuentes customizadas si la codificación binaria original se eliminó. Se inyecta una fuente estándar (`NotoSans`) transparente, restaurando la usabilidad, pero no el aspecto tipográfico de la letra dañada (que permanece visualmente idéntica al PDF original).

## 🛣️ Roadmap v1.1

- Soporte de diccionarios especializados (PIV - Plena Ilustrita Vortaro).
- Mejora de rendimiento y gestión de memoria para PDFs de más de 500 páginas.
- Ampliación a formatos ePub y Mobi.
