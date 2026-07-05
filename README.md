# FISIAgent

Plataforma web de apoyo emocional e inteligencia académica para estudiantes de la **Facultad de Ingeniería de Sistemas e Informática (FISI) — UNSM**. Combina un chatbot conversacional con IA, detección de riesgo psicosocial con un modelo BETO entrenado en español, y recursos de salud mental orientados al contexto universitario peruano.

> Proyecto académico — Asignatura: Tendencias en el Desarrollo de Software | FISI-UNSM | Semestre 2026-1

---

## Tendencias de software aplicadas

Este proyecto aplica cuatro tendencias del **InfoQ Software Architecture and Design Trends Report 2025**, una por cada etapa del modelo *Crossing the Chasm*:

| Etapa | Tendencia | Aplicación en FISIAgent |
|-------|-----------|------------------------|
| 🟢 **Late Majority** | Large Language Models (LLMs) | Gemini 2.5 Flash genera las respuestas empáticas del chatbot |
| 🟡 **Early Majority** | AI-assisted development | Uso de GitHub Copilot y BETO como modelo especializado en lugar de uno genérico; prompts de sistema como guías arquitectónicas |
| 🟠 **Early Adopters** | Retrieval-Augmented Generation (RAG) | El chatbot consulta documentos reales de la FISI-UNSM (reglamento, sílabos, calendario) antes de responder |
| 🔴 **Innovators** | Agentic AI | Flujo multi-agente: AgenteEvaluadorRiesgo (BETO) + AgenteRAG + AgenteRespondedor (Gemini) + AgenteCrisis |

---

## Decisiones de arquitectura

### Arquitectura Hexagonal (Ports & Adapters)

El backend sigue el patrón de **Arquitectura Hexagonal** para aislar el dominio de los detalles de infraestructura:

```
FISIAgent-Back/
  app/
    core/           ← Dominio: lógica de riesgo, reglas de agentes
    ports/          ← Contratos (interfaces Python) para NLP, LLM, RAG
    adapters/
      inbound/      ← routes/ — FastAPI como puerto de entrada HTTP
      outbound/     ← services/ — BETO, Gemini, ChromaDB como puertos de salida
```

### Diseño nativo para la nube

- Contenedores Docker independientes para backend y frontend
- Variables de entorno para toda configuración sensible (sin secrets en código)
- Volúmenes para el modelo BETO (~420 MB) y la base de datos vectorial ChromaDB
- Desplegable en Railway, Render o cualquier plataforma cloud con soporte Docker

---

## Características principales

- **Chat con IA** — Conversación empática en tiempo real usando Gemini 2.5 Flash con rol de apoyo psicológico orientado al estudiante universitario.
- **Detección de riesgo psicosocial** — Modelo BETO con fine-tuning clasifica cada mensaje en tres niveles: Control, Moderado y Crítico.
- **RAG académico FISI-UNSM** — Responde preguntas sobre reglamento, horarios, sílabos y recursos de bienestar con información real de la universidad.
- **Pipeline multi-agente** — Agentes especializados deciden autónomamente el flujo: evaluar riesgo → buscar en docs → responder o escalar a crisis.
- **Intervención adaptativa** — Popup de video (nivel Moderado) o protocolo de crisis con Línea 113 (nivel Crítico).
- **Registro de ánimo** — Calendario interactivo con gráficos para seguimiento del estado emocional diario.

---

## Stack tecnológico

| Capa | Tecnología |
|------|-----------|
| Frontend | React 19 + Vite |
| Backend | FastAPI (Python) + Uvicorn |
| IA Conversacional | Google Gemini 2.5 Flash |
| Clasificación de riesgo | BETO (BERT en español) con fine-tuning |
| RAG — Base vectorial | ChromaDB + sentence-transformers |
| RAG — Orquestación | LangChain |
| HTTP cliente | Axios |
| Validación de datos | Pydantic v2 |
| Contenedores | Docker + Docker Compose |

---

## Arquitectura del sistema

```
Usuario
   │
   ▼
React Frontend (puerto 5173)
   │  POST /chatai  { history: [...] }
   ▼
FastAPI Backend (puerto 8000)
   │
   ├─ AgenteEvaluadorRiesgo  ← BETO clasifica el mensaje
   │    └─ nivel: "control" | "moderado" | "critico"
   │
   ├─ AgenteRAG              ← ChromaDB busca en docs FISI-UNSM
   │    └─ fragmentos relevantes del reglamento / sílabos / FAQ
   │
   ├─ AgenteRespondedor      ← Gemini genera la respuesta empática
   │    └─ usa el nivel de riesgo + contexto RAG
   │
   └─ AgenteCrisis           ← se activa si nivel == "critico"
        └─ protocolo Línea 113
   │
   ▼
Response: { respuesta, nivel_riesgo, video_sugerido, probabilidades, fuentes_rag }
   │
   ▼
Frontend decide qué mostrar:
   ├─ "control"  → solo respuesta en el chat
   ├─ "moderado" → respuesta + VideoPopup con video de ayuda
   └─ "critico"  → respuesta + CrisisOverlay (Línea 113)
```

---

## Modelo BETO — Clasificación de riesgo

### Descripción

Modelo `BertForSequenceClassification` basado en BETO (BERT en español), con fine-tuning sobre un dataset de comentarios de YouTube etiquetados con niveles de riesgo psicosocial.

| Label | Clase | Descripción |
|-------|-------|-------------|
| 0 | Control | Sin señales de riesgo |
| 1 | Moderado | Estrés o ansiedad detectados |
| 2 | Crítico | Indicadores de crisis o riesgo grave |

### Métricas (5-fold CV, n = 1,998 muestras)

| Clase | Precision | Recall | F1 | AUC-ROC |
|-------|-----------|--------|----|---------|
| Control | 0.926 | 0.922 | 0.924 | 0.821 |
| Moderado | 0.429 | 0.352 | 0.387 | 0.732 |
| Crítico | 0.326 | 0.500 | 0.394 | 0.834 |
| **Macro avg** | 0.560 | 0.591 | **0.568** | — |
| **Accuracy** | — | — | — | **0.843** |

**Macro F1 (5-fold):** `0.5685 ± 0.0408`

### Estrategia de umbrales

El modelo usa las probabilidades de softmax con umbrales ajustados al desbalance del dataset (≈85% Control):

```
P(Crítico)  ≥ 0.30  →  nivel "critico"   (umbral bajo para priorizar recall)
P(Moderado) ≥ 0.45  →  nivel "moderado"
Default              →  nivel "control"
```

Si el modelo no puede cargarse, el sistema degrada automáticamente a detección por palabras clave como red de seguridad.

---

## Estructura del proyecto

```
FISIAgent-project/
│
├── BETO_model/                     # Pesos y configuración del modelo entrenado
│   ├── config.json                 # Arquitectura del modelo (BERT, 3 clases)
│   ├── model.safetensors           # Pesos del modelo (~420 MB)
│   ├── tokenizer.json              # Tokenizador BERT en español
│   ├── tokenizer_config.json       # Configuración del tokenizador
│   └── training_args.bin           # Argumentos de entrenamiento
│
├── FISIAgent-Back/                 # Backend FastAPI — Arquitectura Hexagonal
│   ├── app/
│   │   ├── main.py                 # Punto de entrada + carga del modelo (lifespan)
│   │   ├── core/                   # [En desarrollo] Dominio: lógica de agentes
│   │   ├── ports/                  # [En desarrollo] Contratos/interfaces
│   │   ├── services/
│   │   │   ├── nlp.py              # Servicio BETO: cargar_modelo(), clasificar_riesgo()
│   │   │   └── rag.py              # [En desarrollo] Pipeline RAG con ChromaDB
│   │   ├── routes/
│   │   │   ├── gemini.py           # POST /chatai — chat + clasificación de riesgo
│   │   │   ├── chat.py             # POST /chat — chat básico por palabras clave
│   │   │   ├── crisis.py           # POST /crisis — detección de crisis
│   │   │   ├── recursos.py         # GET /recursos — búsqueda por distrito
│   │   │   └── health.py           # GET /health — health check
│   │   ├── models/
│   │   │   └── chat.py             # Modelos Pydantic
│   │   ├── docs/                   # [En desarrollo] Documentos FISI-UNSM para RAG
│   │   │   ├── reglamento.pdf
│   │   │   ├── plan_estudios.pdf
│   │   │   └── faq_bienestar.txt
│   │   ├── M04_GestorRecursos.py   # Gestor de recursos por distrito
│   │   └── recursos_lima.json      # Base de datos de recursos en Lima
│   └── requirements.txt
│
└── FISIAgent-Front/                 # Frontend React + Vite
    └── src/
        ├── pages/
        │   ├── ChatPage.jsx         # Chat principal
        │   ├── MoodLogPage.jsx      # Registro de ánimo
        │   └── ResourcesPage.jsx    # Recursos de apoyo
        ├── components/
        │   ├── CrisisOverlay.jsx    # Modal de emergencia (nivel Crítico)
        │   ├── VideoPopup.jsx       # Popup de video (nivel Moderado)
        │   └── Message.jsx          # Burbuja de mensaje
        ├── services/
        │   └── api.js               # Cliente HTTP (Axios)
        └── styles/
            └── global.css
```

---

## Instalación y configuración

### Requisitos previos

- Python 3.10+
- Node.js 18+
- pip
- [Git LFS](https://git-lfs.com/) — necesario para descargar el modelo BETO (~420 MB)

---

### Paso 1 — Instalar Git LFS y clonar el repositorio

Git LFS almacena archivos grandes fuera del repositorio pero los descarga automáticamente al clonar.

```bash
# Instalar Git LFS (solo la primera vez en cada máquina)
git lfs install

# Clonar el repositorio (descarga automáticamente BETO_model/)
git clone https://github.com/kevinccana/JoinAI-project.git
cd FISIAgent-project
```

> Si ya clonaste el repo antes de que LFS estuviera configurado, ejecuta `git lfs pull` para descargar el modelo.

---

### Paso 2 — Configurar el modelo BETO

El modelo se descarga automáticamente con el clone. Verifica que la carpeta exista:

```
FISIAgent-project/
└── BETO_model/
    ├── config.json
    ├── model.safetensors   ← ~420 MB
    ├── tokenizer.json
    ├── tokenizer_config.json
    └── training_args.bin
```

Si la carpeta está vacía o no existe, fórzala a descargar:

```bash
git lfs pull
```

---

### Paso 3 — Configurar el backend

```bash
cd FISIAgent-Back

# Crear entorno virtual
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Linux / Mac

# Instalar dependencias (incluye torch, transformers, safetensors)
pip install -r requirements.txt
```

Crear el archivo `.env` con la API key de Gemini:

```bash
# FISIAgent-Back/.env
GEMINI_API_KEY=tu_api_key_aqui
```

> Obtén tu API key gratis en [Google AI Studio](https://aistudio.google.com/app/apikey).  
> Nunca subas el `.env` al repositorio — ya está en el `.gitignore`.

---

### Paso 4 — Iniciar el backend

```bash
# Desde FISIAgent-Back/
python -m uvicorn app.main:app --reload
```

Al arrancar verás:
```
[Startup] Cargando modelo BETO...
[BETO] Modelo cargado correctamente y listo para inferencia.
[Startup] BETO listo. Clasificación de riesgo activa.
```

> Si `BETO_model/` no está presente, el servidor igual arranca en modo fallback (detección por palabras clave).

---

### Paso 5 — Iniciar el frontend

En una terminal separada:

```bash
cd FISIAgent-Front
npm install
npm run dev
```

La aplicación estará disponible en `http://localhost:5173`.

---

## Variables de entorno

| Variable | Descripción | Requerida |
|----------|-------------|-----------|
| `GEMINI_API_KEY` | API key de Google Gemini | Sí |

> **Seguridad:** Nunca pongas la API key directamente en el código (`os.getenv("AIzaSy...")`).
> Siempre usa `os.getenv("GEMINI_API_KEY")` con el valor en `.env`.
> Si la key fue expuesta en un commit, [regénérala](https://aistudio.google.com/app/apikey) de inmediato.

---

## API Endpoints

| Método | Ruta | Descripción |
|--------|------|-------------|
| `POST` | `/chatai` | Chat con Gemini + clasificación de riesgo con BETO |
| `POST` | `/chat` | Chat básico por palabras clave |
| `POST` | `/crisis` | Detección de crisis (standalone) |
| `GET` | `/recursos` | Búsqueda de recursos por distrito en Lima |
| `GET` | `/health` | Health check del servidor |
| `GET` | `/` | Estado general de la API |

### Ejemplo — POST /chatai

**Request:**
```json
{
  "history": [
    { "role": "user", "text": "Hola" },
    { "role": "model", "text": "Hola, soy FISIAgent. ¿Cómo te sientes hoy?" },
    { "role": "user", "text": "Me siento muy ansioso, no puedo con todo" }
  ]
}
```

**Response:**
```json
{
  "respuesta": "Entiendo que estás sintiendo una carga muy grande...",
  "nivel_riesgo": "moderado",
  "video_sugerido": {
    "tipo": "mindfulness",
    "titulo": "Mindfulness para principiantes",
    "descripcion": "5 minutos de atención plena para reducir el estrés",
    "url": "https://www.youtube.com/watch?v=3oCC4NDgYrY&t=17s",
    "duracion": "5 min"
  },
  "probabilidades": {
    "control": 0.1823,
    "moderado": 0.6241,
    "critico": 0.1936
  }
}
```

---

## Recursos de emergencia

La aplicación está diseñada para el contexto peruano. En caso de crisis se muestra:

- **Línea 113 — Opción 5** — Salud Mental, gratuita, disponible 24/7 en todo el país.

---

## Estado del proyecto

| Funcionalidad | Estado |
|--------------|--------|
| Chat con Gemini | ✅ Funcional |
| Clasificación de riesgo con BETO | ✅ Funcional |
| Protocolo de crisis (CrisisOverlay) | ✅ Funcional |
| Popup de video (nivel Moderado) | ✅ Funcional |
| Registro de ánimo | ✅ Interfaz lista, sin persistencia |
| Recursos por distrito | ✅ Funcional (SJL, Comas, Lima Centro) |
| RAG con docs FISI-UNSM | 🔄 En desarrollo |
| Pipeline multi-agente (Agentic AI) | 🔄 En desarrollo |
| Arquitectura Hexagonal completa | 🔄 En desarrollo |
| Docker + despliegue en nube | 🔄 En desarrollo |
| Autenticación de usuarios | ⏳ Pendiente |
| Base de datos persistente | ⏳ Pendiente |
