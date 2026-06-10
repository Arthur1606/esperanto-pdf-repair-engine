# Esperanto Language Engine (PDF Repair Module)

Un motor de procesamiento del lenguaje natural **100% offline (air-gapped)** y determinista, enfocado actualmente en su módulo primario: reparar PDFs de Esperanto que sufren de corrupción en la codificación de caracteres.

---

## 🏆 Resultados de la Fase B (Motor Contextual)

El motor cuenta con un pipeline analítico que no depende de LLMs ni APIs externas. Durante las pruebas de la Fase B:
- **Volumen de Prueba:** 30 lecciones reales.
- **Automatización:** **97.10%** (234 casos de ambigüedad severa resueltos de manera automática).
- **Seguridad (Anti-Alucinaciones):** 7 casos (2.90%) protegidos por el umbral de seguridad estricto (0.85) y enviados a revisión manual.
- **Naturaleza del Pipeline:** 0% IA Generativa, 0% APIs externas, 100% Offline, $O(1)$ heurístico.

---

## 📖 Descripción

### El Problema
Al generar o imprimir documentos PDF antiguos, los caracteres especiales del Esperanto con circunflejo (ĉ, ĝ, ĥ, ĵ, ŝ, ŭ) suelen perder su codificación. Son reemplazados por glifos corruptos, caracteres de otros idiomas, o transliteraciones híbridas (X-System/H-System). Esto destruye la indexación y la capacidad de búsqueda (Copy & Paste / CTRL+F).

### La Solución: Language Engine
Más que un simple parcheador de PDFs, este proyecto es un **Language Engine** especializado en morfología, n-gramas contextuales y reglas bilingües del Esperanto. Su objetivo es restaurar de forma masiva bibliotecas digitales sin comprometer la privacidad de los documentos.

---

## ✨ Características Principales

- **Auditoría Automática:** Escaneo veloz de fuentes incrustadas (CMAP) y conteo de caracteres dañados.
- **Reparación Unicode:** Restauración morfológica profunda de palabras declinadas, plurales o transliteradas.
- **Procesamiento Masivo:** Carga y reparación en lote de decenas de documentos PDF en paralelo.
- **Revisión Manual:** Interfaz interactiva para revisar y aprobar decisiones de baja confianza (falsos positivos).
- **Motor Offline:** Cachés de frecuencia locales, corpus de Tatoeba (14 MB) y diccionarios Hunspell nativos.

---

## 🏗 Arquitectura (Arkitekturo Heuristic Cascade)

El sistema procesa el texto a través de un esquema en cascada heurístico (7 Capas) antes de reinyectarlo en el formato final:

| Capa | Nombre | Función Principal |
| :---: | :--- | :--- |
| **0** | **Text Extraction** | Extracción PyMuPDF y auditoría base de fuentes y glifos. |
| **1** | **Radiko Layer** | *Dictionary Exact Match.* Recuperación rápida de vocabulario determinista. |
| **2** | **Morfo Layer** | Análisis morfológico y validación ortográfica mediante Hunspell nativo. |
| **3** | **Frekvenco Layer** | *Unigram Frequency.* Caché local para desempate estadístico de palabras. |
| **4** | **Kunteksto Layer** | *Contextual N-grams.* Uso de corpus offline de 14 MB (1.5M N-gramas). |
| **5** | **Gramatiko Layer** | *Grammar & Bilingual.* Inferencia usando reglas de Esperanto y traducción. |
| **6** | **Jugxanto Layer** | *Final Resolution.* Combinación de scores. Delega a humano si `score < 0.85`. |
| **7** | **Restarigo Layer** | *Text Injection.* Reinyección invisible en el PDF preservando maquetación. |

---

## 🚀 Tecnologías

- **Backend:** Python (Core Pipeline), FastAPI (RESTful), SQLite, PyMuPDF, Spylls/Hunspell.
- **Frontend:** Next.js, TypeScript, Tailwind CSS.

---

## 🖥️ Instalación y Ejecución Rápida

El sistema opera como un microservicio dual local. Requiere **Python 3.9+** y **Node.js v18+**.

```bash
# 1. Clonar el repositorio
git clone https://github.com/Arthur1606/esperanto-pdf-repair-engine.git
cd esperanto-pdf-repair-engine

# 2. Levantar la API (Backend)
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --host 127.0.0.1 --port 8000 &

# 3. Levantar la Interfaz (Frontend)
cd ../frontend
npm install
npm run dev
```

*Accede al dashboard en: [http://localhost:3000](http://localhost:3000)*

### 🕹️ Flujo de Uso
1. **Subir PDF:** Carga el documento defectuoso.
2. **Auditar:** El servidor extrae metadata y evalúa calidad.
3. **Reparar:** Pasa por la cascada heurística e incrusta la fuente base (`NotoSans`).
4. **Resolver:** Dirígete a *Manual Review* si hay palabras de baja confianza.
5. **Descargar:** Obtén la versión corregida (`[↓ Auto]` o `[↓ Review]`).

---

## 🛣️ Roadmap del Proyecto (Fases A-F)

- ✅ **Fase A:** Extracción Base, Detección de Glifos y Recuperación Hunspell. *(Completado)*
- ✅ **Fase B:** Motor Contextual N-Gramas (Kunteksto) y Reglas Bilingües (Gramatiko). *(Completado)*
- ⏳ **Fase C:** Soporte para PIV (Plena Ilustrita Vortaro) y optimización de memoria (>500 páginas).
- 📅 **Fase D:** Ampliación a formatos ePub, Mobi y texto plano (desacoplamiento de PDF).
- 📅 **Fase E:** Despliegue distribuido de procesamiento masivo (Batching a nivel Enterprise).
- 📅 **Fase F:** Exposición de la cascada heurística como API externa paquetizada para otros clientes.

---

## ⚠️ Limitaciones Conocidas

- Falsos positivos mínimos cuando hay mezcla deliberada de grandes bloques de texto en español y Esperanto (el detector bilingüe mitiga, pero no es infalible).
- La reinyección inyecta una fuente estándar (`NotoSans`) transparente, restaurando la usabilidad de búsqueda pero dejando el aspecto tipográfico dañado original visualmente idéntico al PDF.
