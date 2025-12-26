# PRD — Sistema RAG Pedagógico para Generación de Preguntas tipo ICFES

## 1. Visión del Producto

Diseñar e implementar un **sistema RAG (Retrieval-Augmented Generation) pedagógico** que permita generar preguntas **originales**, **alineadas a competencias tipo ICFES**, utilizando como fuente estructural un **CSV enriquecido** (preguntas segmentadas + metadatos), sin reutilizar ni transformar directamente contenido restringido.

El sistema debe:
- Aprender **patrones cognitivos**, no textos.
- Generar ítems nuevos, auditables y explicables.
- Servir como base para analítica educativa y productos SaaS futuros.

---

## 2. Objetivos del Sistema

### Objetivos Funcionales
- Generar preguntas originales por:
  - prueba (Sociales, Lectura, Matemáticas, etc.)
  - habilidad (skill)
  - dificultad
- Recuperar conocimiento pedagógico relevante vía RAG.
- Validar automáticamente calidad y similitud.
- Exportar preguntas en formatos estructurados (JSON/CSV).

### Objetivos No Funcionales
- Evitar cualquier forma de copia o parafraseo cercano.
- Ser escalable por prueba y grado.
- Ser auditable (explicabilidad pedagógica).
- Cumplir restricciones legales sobre uso de cartillas ICFES.

---

## 3. Alcance del MVP (In-Scope)

✔ Uso del CSV enriquecido como **fuente estructural**  
✔ RAG pedagógico (skills, distractores, reglas)  
✔ Generación controlada por LLM  
✔ Validación automática (estructura + similitud)  
✔ Persistencia en base de datos  
✔ Pipeline reproducible end-to-end  

🚫 No incluye:
- UI avanzada para estudiantes
- Exámenes adaptativos completos
- Fine-tuning de modelos base (fase futura)

---

## 4. Arquitectura General

### 4.1 Componentes Principales


---

## 5. Fuente de Datos (Input)

### 5.1 CSV Enriquecido
Archivo base:
- `preguntas_sociales_final_enriquecido.csv`

Contiene:
- Estructura del ítem
- Metadatos pedagógicos
- Patrones de distractores
- Flags legales (`is_original`, `allowed_for_training`)

⚠️ **Regla clave**:  
El texto de las preguntas **NO se usa como contexto de generación**, solo como fuente de patrones.

---

## 6. RAG Pedagógico — Diseño

### 6.1 Tipos de Documentos RAG

Todos se almacenan en una tabla única (`rag_documents`) con `doc_type`.

#### A. Skill Cards (`doc_type=skill_card`)
Representan una habilidad evaluable.

**Contenido mínimo:**
- Definición operacional
- Checklist de evidencias
- Errores comunes
- Patrones de distractores recomendados
- Plantillas abstractas (sin texto copiable)

#### B. Distractor Patterns (`doc_type=distractor_pattern`)
Errores plausibles intencionales.

**Contenido mínimo:**
- Nombre del patrón
- Descripción
- Cómo se manifiesta
- Cuándo usarlo
- Anti-pistas

#### C. Blueprint Rules (`doc_type=blueprint_rule`)
Reglas de calidad y estilo por prueba.

Ejemplos:
- “Una sola opción correcta”
- “Evitar absolutos”
- “Opciones de longitud similar”

#### D. Seed Texts (`doc_type=seed_text`)
Contenido permitido:
- Textos propios
- CC0 / CC-BY
- Contextos creados por docentes

---

## 7. Base de Datos

### 7.1 Tabla: `rag_documents`
```sql
id uuid PK
doc_type text
exam text
skill text
topic text
difficulty_band text
content text
metadata jsonb
embedding vector


┌─────────────────────────────────────────────────────────────────────┐
│                           SOURCES / DATA                             │
├─────────────────────────────────────────────────────────────────────┤
│  PDFs (cartillas) ──► Extractor/OCR ──► CSV robusto (ya lo tienes)   │
│                           │                                          │
│                           ▼                                          │
│                   ETL RAG Builder (Python)                           │
│        (crea SkillCards / DistractorPatterns / BlueprintRules)       │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              │  (documentos "pedagógicos", NO ítems)
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         STORAGE / INDEXING                           │
├─────────────────────────────────────────────────────────────────────┤
│  Postgres (Supabase)                                                 │
│   ├─ rag_documents (doc_type, content, metadata, embedding)          │
│   ├─ items_bank (preguntas generadas y aprobadas)                    │
│   ├─ attempts (respuestas de estudiantes) (fase 2)                   │
│   └─ similarity_items (embeddings de ítems restringidos / históricos)│
│                                                                      │
│  Vector Search (pgvector / Supabase Vector)                          │
│   ├─ retrieval: rag_documents                                        │
│   └─ similarity check: similarity_items                              │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                            RAG SERVICE                               │
├─────────────────────────────────────────────────────────────────────┤
│  Backend API (FastAPI)                                               │
│   ├─ /generate                                                       │
│   │    1) Retrieval (skill_card + distractors + rules + seed_text)   │
│   │    2) Prompt assembly                                            │
│   │    3) LLM generation (JSON)                                      │
│   │    4) Validation (estructura/calidad)                            │
│   │    5) Similarity check (bloqueo copia)                           │
│   │    6) Persist (items_bank)                                       │
│   ├─ /validate                                                       │
│   └─ /similarity-check                                               │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         AI PROVIDERS (APIs)                          │
├─────────────────────────────────────────────────────────────────────┤
│  Embeddings API  ──► vectores para retrieval y similarity check       │
│  LLM API         ──► genera pregunta + opciones + explicación (JSON)  │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                          CONSUMERS (MVP UI)                          │
├─────────────────────────────────────────────────────────────────────┤
│  Admin/Docente UI (simple)                                           │
│   ├─ Revisar / editar / aprobar preguntas                            │
│   ├─ Exportar a PDF/CSV                                              │
│   └─ Activar para estudiantes                                        │
│                                                                      │
│  Estudiante UI (fase 2)                                              │
│   └─ Resolver preguntas + telemetría (tiempo, cambios, aciertos)     │
└─────────────────────────────────────────────────────────────────────┘


Piezas mínimas (deployment MVP)
A) Un job “offline” (ETL)

etl_rag_builder.py

Toma tu CSV robusto y produce:

skill_cards (doc_type=skill_card)

distractor_patterns (doc_type=distractor_pattern)

blueprint_rules (doc_type=blueprint_rule)

(opcional) seed_texts (doc_type=seed_text)

Calcula embeddings y los inserta en rag_documents.

B) Un API (FastAPI)

/generate recibe: exam, skill, difficulty, topic, n_items

hace retrieval + generación + validación + similarity-check

guarda en items_bank y devuelve JSON.

C) Una BD única (Supabase Postgres + pgvector)

Te evita tener Qdrant y Postgres separados en MVP.

Separación crítica: RAG vs Similarity Index

RAG (rag_documents): solo conocimiento pedagógico + reglas + semillas permitidas.

Similarity (similarity_items): embeddings de ítems (incluye restringidos si los tienes) solo para bloquear copias.

Esto te protege de que el modelo “vea” preguntas reales y las reescriba.

Flujo de una generación (paso a paso)

API recibe request: “Sociales, comparar argumentos, media, ética”

Retrieval trae:

1 skill card

3 patrones de distractor

3 reglas de blueprint

1 seed_text permitido

Se arma prompt con formato JSON estricto

LLM genera ítem

Validación:

estructura A–D

1 correcta

explicación consistente

Similarity check:

si similitud > umbral → regenerar

Guardar en items_bank + estado (draft/approved)

Qué te recomiendo como “primera entrega” del tech lead

SQL schema (4 tablas): rag_documents, similarity_items, items_bank, generation_runs

ETL que cargue 50 skill cards + 30 patterns + 20 rules

Endpoint /generate con 1 ruta end-to-end



