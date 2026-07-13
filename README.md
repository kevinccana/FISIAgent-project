# FISIAgent

Plataforma web de apoyo emocional e inteligencia académica para estudiantes de la **Facultad de Ingeniería de Sistemas e Informática (FISI) — UNSM**. Combina un chatbot conversacional con IA, detección de riesgo psicosocial con un modelo BETO entrenado en español, un dashboard de bienestar emocional y un planificador de tareas con priorización por IA, orientados al contexto universitario peruano.

El proyecto implementa **3 funcionalidades end-to-end** (frontend + backend + persistencia):

1. **Chat de Apoyo Emocional** — conversación con IA, clasificación de riesgo (BETO) y RAG sobre documentos de la FISI-UNSM.
2. **Dashboard de Bienestar** — registro y seguimiento del estado de ánimo con insights automáticos.
3. **Planificador Inteligente** — gestión de tareas con priorización y recomendaciones generadas por un agente de IA (Gemini).

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

### Arquitectura Hexagonal (Ports & Adapters) ✅ IMPLEMENTADA

El backend implementa completamente el patrón de **Arquitectura Hexagonal** para aislar el dominio de los detalles de infraestructura, cubriendo las 3 funcionalidades (Chat, Mood, Tasks):

```
FISIAgent-Back/
  app/
    core/                                    # 🎯 DOMINIO (lógica de negocio)
      domain/
        models.py                            # Entidades del Chat: Message, RiskAssessment, ChatResponse
        mood_models.py                       # Entidades del Dashboard: MoodEntry, MoodStatistics, MoodLevel
        task_models.py                       # Entidades del Planificador: Task, Reminder, TaskPriority, TaskStatus, DailySchedule
        agent.py                             # Contrato base de agente (AgentRole)
        exceptions.py                        # Excepciones del dominio
      agents/                                # 🤖 Sistema multi-agente (Agentic AI)
        coordinator_agent.py                 # CoordinadorAgente (supervisor)
        risk_analyzer_agent.py               # Clasifica riesgo con BETO
        rag_retriever_agent.py               # Recupera contexto de ChromaDB
        empathy_responder_agent.py           # Genera respuesta empática con Gemini
        planner_agent.py                     # Prioriza tareas y analiza agenda con Gemini
      use_cases/
        process_conversation.py              # Caso de uso: Chat (flujo simple)
        process_conversation_with_agents.py  # Caso de uso: Chat vía sistema multi-agente
        mood_use_cases.py                    # 6 casos de uso del Dashboard de Bienestar
        task_use_cases.py                    # 10 casos de uso del Planificador Inteligente

    ports/                                   # 🔌 CONTRATOS (interfaces)
      inbound/
        chat_service.py                      # Puerto de entrada: ChatServicePort
      outbound/
        risk_classifier.py                   # RiskClassifierPort
        llm_service.py                       # LLMServicePort
        video_recommender.py                 # VideoRecommenderPort
        rag_service.py                       # RAGServicePort
        mood_repository.py                   # MoodLogRepositoryPort
        task_repository.py                   # TaskRepositoryPort

    adapters/                                # 🔧 ADAPTADORES (implementaciones)
      inbound/
        api/
          chat_router.py                     # POST /chatai
          mood_router.py                     # /mood/* (Dashboard de Bienestar)
          task_router.py                     # /tasks/* (Planificador Inteligente)
      outbound/
        beto_adapter.py                      # Implementa RiskClassifierPort con BETO
        gemini_adapter.py                    # Implementa LLMServicePort con Gemini
        video_recommender_adapter.py         # Implementa VideoRecommenderPort
        rag_adapter.py                       # Implementa RAGServicePort con ChromaDB
        sqlite_mood_repository.py            # Implementa MoodLogRepositoryPort con SQLite
        sqlite_task_repository.py            # Implementa TaskRepositoryPort con SQLite (tasks + reminders)

    routes/                                  # Rutas legacy (compatibilidad, pre-hexagonal)
    main.py                                  # Bootstrap + inyección de dependencias (lifespan)
```

**Principios aplicados:**
- ✅ Inversión de dependencias (SOLID-D): El core NO depende de infraestructura
- ✅ Separación de responsabilidades: Cada capa tiene un propósito claro
- ✅ Testabilidad: Los ports permiten mocks fáciles para pruebas
- ✅ Intercambiabilidad: Cambiar BETO/SQLite por otra implementación solo requiere un nuevo adapter

### Diseño nativo para la nube ✅ IMPLEMENTADO

- ✅ Backend dockerizado (`Dockerfile` en la raíz), listo para correr en cualquier plataforma con soporte Docker
- ✅ Variables de entorno para toda configuración sensible (`GEMINI_API_KEY`, `FRONTEND_URL`, `BETO_MODEL_PATH`, `VITE_API_URL`) — sin secrets en código
- ✅ CI/CD con GitHub Actions: push a `main` despliega backend y frontend automáticamente
- ✅ Frontend estático desplegado en GitHub Pages
- ✅ Backend (FastAPI + BETO + RAG) desplegado como contenedor Docker en Hugging Face Spaces

Ver la sección [Despliegue en la nube](#despliegue-en-la-nube) para la arquitectura completa y los pasos de configuración.

---

## Características principales

- **Chat con IA** — Conversación empática en tiempo real usando Gemini 2.5 Flash con rol de apoyo psicológico orientado al estudiante universitario.
- **Detección de riesgo psicosocial** — Modelo BETO con fine-tuning clasifica cada mensaje en tres niveles: Control, Moderado y Crítico.
- **RAG académico FISI-UNSM** — Responde preguntas sobre reglamento, horarios, sílabos y recursos de bienestar con información real de la universidad.
- **Pipeline multi-agente** — Agentes especializados deciden autónomamente el flujo: evaluar riesgo → buscar en docs → responder o escalar a crisis.
- **Intervención adaptativa** — Popup de video (nivel Moderado) o protocolo de crisis con Línea 113 (nivel Crítico).
- **Registro de ánimo** — Calendario interactivo con gráficos para seguimiento del estado emocional diario, conectado a la persistencia SQLite del backend, con insights y recomendaciones automáticas.
- **Planificador Inteligente** — CRUD de tareas con fecha límite, categoría y horas estimadas; un agente de IA (PlannerAgent) sugiere la prioridad, analiza la carga de la agenda diaria y da recomendaciones de organización.

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
| Contenedores | Docker |
| Hosting backend | Hugging Face Spaces (SDK Docker) |
| Hosting frontend | GitHub Pages |
| CI/CD | GitHub Actions |

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
├── BETO_model/                        # NO versionado en este repo (ver nota abajo).
│   ├── config.json                    # Se descarga desde huggingface.co/kevinccana/FisiAgent-BETO
│   ├── model.safetensors              # para desarrollo local, y el Dockerfile lo clona
│   ├── tokenizer.json                 # de ahí mismo durante el build del contenedor.
│   ├── tokenizer_config.json
│   └── training_args.bin
│
├── FISIAgent-Back/                        # Backend FastAPI — Arquitectura Hexagonal
│   ├── app/
│   │   ├── main.py                        # Punto de entrada + bootstrap/DI (lifespan)
│   │   ├── core/                          # Dominio: modelos, agentes y casos de uso (ver árbol arriba)
│   │   ├── ports/                         # Contratos/interfaces (inbound + outbound)
│   │   ├── adapters/                      # Implementaciones concretas (inbound + outbound)
│   │   ├── docs/fisi/                     # Documentos FISI-UNSM para RAG
│   │   │   ├── reglamento_bienestar.txt
│   │   │   ├── plan_estudios.txt
│   │   │   └── faq_estudiantes.txt
│   │   ├── services/
│   │   │   └── nlp.py                     # Servicio BETO: cargar_modelo(), clasificar_riesgo()
│   │   ├── routes/                        # Rutas legacy (compatibilidad, pre-hexagonal)
│   │   │   ├── gemini.py                  # POST /chatai (legacy) — chat + clasificación de riesgo
│   │   │   ├── chat.py                    # POST /chat — chat básico por palabras clave
│   │   │   ├── crisis.py                  # POST /crisis — detección de crisis
│   │   │   ├── recursos.py                # GET /recursos — búsqueda por distrito
│   │   │   └── health.py                  # GET /health — health check
│   │   ├── models/
│   │   │   └── chat.py                    # Modelos Pydantic legacy
│   │   ├── M04_GestorRecursos.py          # Gestor de recursos por distrito
│   │   └── recursos_lima.json             # Base de datos de recursos en Lima
│   ├── fisiagent.db                       # SQLite (mood logs + tasks + reminders), autogenerada
│   └── requirements.txt
│
└── FISIAgent-Front/                        # Frontend React + Vite
    └── src/
        ├── pages/
        │   ├── ChatPage.jsx                # Chat principal
        │   ├── MoodLogPage.jsx             # Registro de ánimo (Dashboard de Bienestar)
        │   ├── TaskPlannerPage.jsx         # Planificador Inteligente (tareas + IA)
        │   └── ResourcesPage.jsx           # Recursos de apoyo
        ├── components/
        │   ├── CrisisOverlay.jsx           # Modal de emergencia (nivel Crítico)
        │   ├── VideoPopup.jsx              # Popup de video (nivel Moderado)
        │   └── Message.jsx                 # Burbuja de mensaje
        ├── services/
        │   └── api.js                      # Cliente HTTP (Axios): chat, mood y tasks
        └── styles/
            └── global.css
```

---

## Instalación y configuración

### Requisitos previos

- Python 3.10+
- Node.js 18+
- pip
- [Git LFS](https://git-lfs.com/) — necesario para los binarios que sí viven en este repo (video de `CrisisOverlay`, sprites de `MoodLogPage`)
- [Git](https://git-scm.com/) para clonar el modelo BETO desde su propio repo en el Hub (paso 2)

---

### Paso 1 — Instalar Git LFS y clonar el repositorio

Git LFS almacena archivos grandes fuera del repositorio pero los descarga automáticamente al clonar.

```bash
# Instalar Git LFS (solo la primera vez en cada máquina)
git lfs install

git clone https://github.com/kevinccana/FISIAgent-project.git
cd FISIAgent-project
```

> Si ya clonaste el repo antes de que LFS estuviera configurado, ejecuta `git lfs pull` para descargar los binarios (video, sprites).

---

### Paso 2 — Descargar el modelo BETO

El modelo **no vive en este repositorio** — tiene su propio repo de modelo en el Hub de Hugging Face para no inflar el historial de Git de FISIAgent-project con ~420 MB de pesos. Para desarrollo local, clónalo directamente en la raíz del proyecto:

```bash
# Desde la raíz de FISIAgent-project/
git clone https://huggingface.co/kevinccana/FisiAgent-BETO BETO_model
```

Verifica que quede así:

```
FISIAgent-project/
└── BETO_model/
    ├── config.json
    ├── model.safetensors   ← ~420 MB
    ├── tokenizer.json
    ├── tokenizer_config.json
    └── training_args.bin
```

`BETO_model/` está en `.gitignore` — no hace falta (ni se debe) commitear esta carpeta. Si prefieres otra ubicación, apunta `BETO_MODEL_PATH` ahí (ver [Variables de entorno](#variables-de-entorno)). El `Dockerfile` hace este mismo `git clone` automáticamente durante el build, así que en producción no necesitas hacer nada extra.

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

> **Nuevas dependencias (RAG + Agentic AI):**
> - `langchain`, `langchain-community` - Pipeline de documentos
> - `chromadb` - Base de datos vectorial
> - `sentence-transformers` - Embeddings multilingües
> 
> Si encuentras errores en la instalación de ChromaDB en Windows, ejecuta:
> ```bash
> pip install --upgrade chromadb
> ```

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

Al arrancar verás los siguientes logs indicando la correcta inicialización:

```
[Startup] Inicializando FISIAgent - Hexagonal + Agentic AI + RAG...
[Startup] Cargando modelo BETO...
[BETO] Modelo cargado correctamente y listo para inferencia.
[Startup] ✓ BETO cargado correctamente
[Startup] Inicializando RAG con ChromaDB...
[Startup] Cargando documentos FISI-UNSM para RAG...
[Startup] ✓ Cargados 3 documentos
[Startup] ✓ Generados X chunks
[Startup] ✓ RAG inicializado correctamente
[Startup] Creando sistema multi-agente...
[Startup] ✓ Sistema multi-agente inicializado (3 agentes + coordinador)
[Startup] ✓ Caso de uso con agentes inicializado
[Startup] ✓ API router configurado con sistema de agentes
[Startup] 🚀 FISIAgent listo
[Startup] 📊 Tendencias InfoQ 2025 implementadas:
[Startup]    🔴 Innovators: Agentic AI (Multi-Agent)
[Startup]    🟠 Early Adopters: RAG (ChromaDB + LangChain)
[Startup]    🟡 Early Majority: AI-assisted development
[Startup]    🟢 Late Majority: LLMs (Gemini 2.5 Flash)
```

**Verificar que RAG funciona:**
- Se crea automáticamente el directorio `chroma_db/` con la base vectorial persistida
- Los documentos en `app/docs/fisi/` se cargan y dividen en chunks
- Si ves `[Startup] ⚠ RAG no disponible`, verifica que los archivos .txt existan

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

| Variable | Descripción | Requerida | Dónde se usa |
|----------|-------------|-----------|--------------|
| `GEMINI_API_KEY` | API key de Google Gemini | Sí | Backend |
| `FRONTEND_URL` | Orígenes adicionales permitidos por CORS (ej. la URL de GitHub Pages), separados por coma | No — sin ella solo funciona con `localhost:5173` | Backend |
| `BETO_MODEL_PATH` | Ruta absoluta a `BETO_model/` dentro del contenedor | No — por defecto busca `BETO_model/` en la raíz del repo | Backend |
| `VITE_API_URL` | URL pública del backend, usada al compilar el frontend | No — por defecto `http://localhost:8000` | Frontend (build) |

> **Seguridad:** Nunca pongas la API key directamente en el código (`os.getenv("AIzaSy...")`).
> Siempre usa `os.getenv("GEMINI_API_KEY")` con el valor en `.env`.
> Si la key fue expuesta en un commit, [regénérala](https://aistudio.google.com/app/apikey) de inmediato.

---

## Despliegue en la nube

Backend y frontend se despliegan por separado y de forma independiente, cada uno disparado por un workflow de GitHub Actions al hacer push a `main`:

```
git push a main
   │
   ├─ .github/workflows/sync-to-hf.yml  ──▶  Hugging Face Spaces (SDK Docker)
   │    (mirror del repo + Dockerfile raíz)      → backend FastAPI + BETO + RAG
   │                                              → escucha en el puerto 7860
   │
   └─ .github/workflows/deploy-pages.yml ──▶  GitHub Pages
        (npm run build con VITE_API_URL)          → frontend estático (React/Vite)
```

### Por qué Hugging Face Spaces para el backend

El backend carga `torch` + `transformers` + `sentence-transformers` + el modelo BETO (~420 MB) en memoria — eso no entra cómodo en el free tier de la mayoría de plataformas (ej. Render free da 512 MB de RAM). El tier gratuito de Spaces (Docker, CPU básico) da bastante más margen y no pide tarjeta de crédito.

**Limitaciones a tener en cuenta:**
- El disco del Space es efímero: `fisiagent.db` (mood logs + tasks) y `chroma_db/` se reinician en cada rebuild, salvo que actives el add-on de pago de *Persistent Storage*.
- El Space "duerme" tras un rato de inactividad y tarda unos segundos en despertar (cold start) en la primera consulta.
- Si el modelo BETO no llegara a cargar por algún motivo, el sistema ya tiene un fallback automático a detección por palabras clave (no se cae, degrada).

### Guía completa paso a paso

La configuración inicial (crear el Space, generar el token de Hugging Face, secrets/variables en GitHub, habilitar Pages), la verificación de que todo quedó corriendo y una sección de troubleshooting con los errores más comunes (CORS, Git LFS, pantalla en blanco, etc.) están documentados en detalle en **[DEPLOYMENT.md](DEPLOYMENT.md)**.

Los workflows viven en [.github/workflows/sync-to-hf.yml](.github/workflows/sync-to-hf.yml) y [.github/workflows/deploy-pages.yml](.github/workflows/deploy-pages.yml).

---

## API Endpoints

### Chat de Apoyo Emocional

| Método | Ruta | Descripción |
|--------|------|-------------|
| `POST` | `/chatai` | Chat con Gemini + clasificación de riesgo con BETO + RAG |
| `POST` | `/chat` | Chat básico por palabras clave (legacy) |
| `POST` | `/crisis` | Detección de crisis (standalone) |
| `GET` | `/recursos` | Búsqueda de recursos por distrito en Lima |

### Dashboard de Bienestar (Mood Logs)

| Método | Ruta | Descripción |
|--------|------|-------------|
| `POST` | `/mood/register` | Registrar estado de ánimo |
| `GET` | `/mood/history/{user_id}` | Historial de registros (últimos N días) |
| `GET` | `/mood/calendar/{user_id}/{year}/{month}` | Calendario mensual para UI |
| `GET` | `/mood/insights/{user_id}` | Estadísticas + insights + recomendaciones |
| `PUT` | `/mood/{entry_id}` | Actualizar registro existente |
| `DELETE` | `/mood/{entry_id}` | Eliminar registro |

### Planificador Inteligente (Tasks)

| Método | Ruta | Descripción |
|--------|------|-------------|
| `POST` | `/tasks/` | Crear tarea (con sugerencia de prioridad por IA opcional) |
| `GET` | `/tasks/upcoming/{user_id}` | Tareas próximas a vencer, ordenadas por urgencia |
| `GET` | `/tasks/overdue/{user_id}` | Tareas vencidas |
| `GET` | `/tasks/statistics/{user_id}` | Estadísticas de productividad (completitud, tendencia) |
| `GET` | `/tasks/schedule/{user_id}/{target_date}` | Análisis de la agenda de un día con recomendaciones de IA |
| `GET` | `/tasks/suggestions/{user_id}` | Diagnóstico y recomendaciones de organización con IA |
| `PUT` | `/tasks/{task_id}` | Actualizar una tarea |
| `POST` | `/tasks/{task_id}/complete` | Marcar tarea como completada |
| `DELETE` | `/tasks/{task_id}` | Eliminar tarea |
| `POST` | `/tasks/reminders` | Crear un recordatorio asociado a una tarea |

### Sistema

| Método | Ruta | Descripción |
|--------|------|-------------|
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

## Probando RAG + Sistema Multi-Agente

El sistema detecta automáticamente si una pregunta requiere contexto académico y activa el agente RAG:

### Ejemplo 1 - Pregunta académica (activa RAG)

**Request:**
```json
{
  "history": [
    { "role": "user", "text": "¿Cuántos créditos mínimos debo llevar por ciclo?" }
  ]
}
```

**Flujo interno:**
1. **CoordinadorAgente** detecta keyword "créditos" → activa `RAGRetrieverAgent`
2. **RiskAnalyzerAgent** clasifica riesgo → Control
3. **RAGRetrieverAgent** busca en ChromaDB → recupera chunks de `plan_estudios.txt`
4. **EmpathyResponderAgent** genera respuesta con contexto RAG

**Response:**
```json
{
  "respuesta": "Según el plan de estudios de la FISI-UNSM, el mínimo de créditos por ciclo es 12 y el máximo es 24. Si tienes un promedio ponderado mayor a 14, puedes solicitar sobrecarga de hasta 28 créditos. Es importante que planifiques tu carga académica considerando tu capacidad y bienestar. ¿Hay algo específico sobre tu matrícula que te preocupe?",
  "nivel_riesgo": "control",
  "video_sugerido": null,
  "probabilidades": {
    "control": 0.9123,
    "moderado": 0.0677,
    "critico": 0.0200
  }
}
```

### Ejemplo 2 - Pregunta emocional (sin RAG)

**Request:**
```json
{
  "history": [
    { "role": "user", "text": "Me siento muy ansioso por los exámenes finales" }
  ]
}
```

**Flujo interno:**
1. **CoordinadorAgente** NO detecta keywords académicas → salta RAG
2. **RiskAnalyzerAgent** clasifica → Moderado
3. **EmpathyResponderAgent** genera respuesta empática sin contexto adicional
4. Se recomienda video (nivel Moderado)

**Response:**
```json
{
  "respuesta": "Entiendo que los exámenes finales pueden generar mucha presión. Es completamente normal sentirse ansioso ante situaciones importantes. Te recomiendo que pruebes técnicas de respiración y organices tu tiempo de estudio. También puedes acudir a la Oficina de Bienestar Estudiantil si necesitas apoyo adicional. Recuerda que cuidar tu bienestar es tan importante como estudiar.",
  "nivel_riesgo": "moderado",
  "video_sugerido": {
    "tipo": "respiracion",
    "titulo": "Técnica 4-7-8 para reducir ansiedad",
    "descripcion": "Ejercicio de respiración profunda para calmar la mente en minutos",
    "url": "https://www.youtube.com/watch?v=gz4G31LGyog",
    "duracion": "4 min"
  },
  "probabilidades": {
    "control": 0.2156,
    "moderado": 0.6534,
    "critico": 0.1310
  }
}
```

### Ejemplo 3 - Pregunta mixta (emocional + académica)

**Request:**
```json
{
  "history": [
    { "role": "user", "text": "Estoy muy estresado porque desaprobé un curso por segunda vez, ¿qué pasa si lo desapruebo una tercera vez?" }
  ]
}
```

**Flujo interno:**
1. **CoordinadorAgente** detecta "desaprobé" + "curso" → activa RAG
2. **RiskAnalyzerAgent** clasifica → Moderado
3. **RAGRetrieverAgent** recupera información de `faq_estudiantes.txt`
4. **EmpathyResponderAgent** combina empatía + información oficial

**Response:**
```json
{
  "respuesta": "Entiendo que esta situación te está generando mucho estrés, y es válido sentirte así. Según el reglamento académico de la FISI, desaprobar un curso obligatorio por tercera vez implica la separación temporal de la universidad por un año, pero puedes solicitar reingreso después de ese periodo. Lo importante ahora es que busques apoyo: te recomiendo hablar con tu tutor académico para evaluar estrategias de estudio, y si el estrés está afectando tu rendimiento, la Oficina de Bienestar puede ayudarte. No estás solo en esto.",
  "nivel_riesgo": "moderado",
  "video_sugerido": {
    "tipo": "mindfulness",
    "titulo": "Mindfulness para reducir estrés académico",
    "descripcion": "5 minutos de meditación guiada para estudiantes",
    "url": "https://www.youtube.com/watch?v=3oCC4NDgYrY",
    "duracion": "5 min"
  },
  "probabilidades": {
    "control": 0.1823,
    "moderado": 0.6892,
    "critico": 0.1285
  }
}
```

**Keywords que activan RAG:**
- Académicas: crédito, curso, ciclo, matrícula, nota, desaprobar, retiro, convalidar
- Administrativas: beca, bienestar, psicólogo, reglamento, plan, horario
- Infraestructura: laboratorio, biblioteca, comedor, wifi

---

## Probando Dashboard de Bienestar

### Ejemplo 1 - Registrar estado de ánimo

**Request:** `POST /mood/register`
```json
{
  "user_id": "estudiante_123",
  "mood": 1,
  "note": "Día tranquilo y productivo"
}
```

**Response:** (201 Created)
```json
{
  "id": 1,
  "user_id": "estudiante_123",
  "mood": 1,
  "mood_label": "Bien",
  "note": "Día tranquilo y productivo",
  "timestamp": "2026-07-08T14:30:00"
}
```

**Mood levels:**
- `0` = Muy bien 😊
- `1` = Bien 🙂
- `2` = Mal 😟
- `3` = Muy mal 😢

---

### Ejemplo 2 - Obtener insights automáticos

**Request:** `GET /mood/insights/estudiante_123?days=30`

**Response:**
```json
{
  "statistics": {
    "period_start": "2026-06-08T00:00:00",
    "period_end": "2026-07-08T23:59:59",
    "total_entries": 25,
    "avg_mood": 1.2,
    "mood_distribution": {
      "Muy bien": 8,
      "Bien": 12,
      "Mal": 4,
      "Muy mal": 1
    },
    "most_common_mood": "Bien",
    "mood_trend": "positivo"
  },
  "monthly_history": [
    {"year": 2026, "month": 6, "month_label": "Jun", "avg_mood": 1.3, "entry_count": 22},
    {"year": 2026, "month": 7, "month_label": "Jul", "avg_mood": 1.2, "entry_count": 25}
  ],
  "insights": [
    "🎉 Tu estado de ánimo ha sido mayormente positivo (promedio: 1.2/3.0)",
    "Tu estado más frecuente es 'Bien' (48% del tiempo)",
    "📈 Tu ánimo ha mejorado respecto al mes anterior (+0.1 puntos)"
  ],
  "recommendations": [
    "Sigue registrando tu ánimo para que podamos darte mejores recomendaciones.",
    "Intenta establecer una rutina de sueño regular y hacer ejercicio moderado."
  ]
}
```

**Algoritmo de insights:**
- Detecta tendencias (positivo/neutral/negativo según avg_mood)
- Compara evolución mensual
- Identifica días críticos (muy mal)
- Genera recomendaciones personalizadas
- Alerta si hay patrón preocupante (>= 3 días muy malos)

---

### Ejemplo 3 - Calendario mensual

**Request:** `GET /mood/calendar/estudiante_123/2026/7`

**Response:**
```json
{
  "year": 2026,
  "month": 7,
  "entries": {
    "1": {"mood": 0, "note": "Gran día con amigos"},
    "3": {"mood": 1, "note": "Tranquilo"},
    "5": {"mood": 2, "note": "Estrés por exámenes"},
    "8": {"mood": 0, "note": "Salida con familia"}
  }
}
```

**Uso:** El frontend renderiza un calendario con colores según el mood de cada día.

---

## Probando el Planificador Inteligente

### Ejemplo 1 - Crear tarea con prioridad sugerida por IA

**Request:** `POST /tasks/`
```json
{
  "user_id": "estudiante_123",
  "title": "Entregar proyecto de BD2",
  "description": "Implementar stored procedures y triggers",
  "due_date": "2026-07-15T23:59:00",
  "priority": null,
  "category": "académico",
  "estimated_hours": 8.0,
  "auto_suggest_priority": true
}
```

**Flujo interno:** el `task_router` invoca `CreateTaskUseCase`, que —al recibir `priority: null` y `auto_suggest_priority: true`— delega en el **PlannerAgent**. Este analiza la fecha límite, la categoría y la carga actual de tareas del usuario (vía Gemini) y devuelve la prioridad sugerida antes de persistir la tarea con `SQLiteTaskRepository`.

**Response:** (201 Created)
```json
{
  "id": 1,
  "title": "Entregar proyecto de BD2",
  "priority": 1,
  "priority_label": "Alta",
  "priority_emoji": "🟠",
  "status_label": "Pendiente",
  "urgency_score": 7.0,
  "days_until_due": 7
}
```

### Ejemplo 2 - Análisis de agenda diaria con IA

**Request:** `GET /tasks/schedule/estudiante_123/2026-07-10`

**Response:**
```json
{
  "date": "2026-07-10",
  "total_estimated_hours": 8.0,
  "is_feasible": true,
  "is_overloaded": false,
  "recommendations": [
    "Tu carga del día es manejable (8.0 horas estimadas).",
    "Prioriza el estudio para Redes en las primeras horas del día cuando estás más concentrado.",
    "Después de 4 horas de estudio, toma un descanso de 15-20 minutos antes de continuar."
  ]
}
```

**Algoritmo de urgencia:** cada tarea calcula un `urgency_score` (0.0 a 10.0) combinando el peso de su prioridad (1.0 a 4.0) y la proximidad de la fecha límite (1.0 a 6.0), usado para ordenar la lista de tareas próximas.

### Ejemplo 3 - Sugerencias de organización general

**Request:** `GET /tasks/suggestions/estudiante_123`

**Response:**
```json
{
  "diagnosis": "Tienes una buena gestión de tareas en general, pero hay 2 tareas vencidas que requieren atención inmediata.",
  "recommendations": [
    "Prioriza inmediatamente las 2 tareas vencidas. Si alguna ya no es relevante, cancélala en lugar de dejarla pendiente.",
    "Bloquea tiempo en tu calendario específicamente para tus tareas urgentes o de alta prioridad.",
    "Divide las tareas grandes (>5 horas estimadas) en subtareas más pequeñas para reducir la procrastinación."
  ],
  "critical_tasks_count": 2,
  "overdue_count": 2
}
```

**En el frontend**, la página `TaskPlannerPage.jsx` consume estos tres endpoints junto con el CRUD de tareas para mostrar: lista de tareas (vencidas + próximas) con acciones de completar/eliminar, formulario de creación con checkbox "Sugerir prioridad con IA", panel de estadísticas de 30 días, selector de fecha para analizar la agenda, y botón de sugerencias de organización.

---

## Recursos de emergencia

La aplicación está diseñada para el contexto peruano. En caso de crisis se muestra:

- **Línea 113 — Opción 5** — Salud Mental, gratuita, disponible 24/7 en todo el país.

---

## Estado del proyecto

| Funcionalidad | Estado |
|--------------|--------|
| **Arquitectura Hexagonal** | ✅ **IMPLEMENTADA** |
| **RAG (ChromaDB + LangChain)** | ✅ **IMPLEMENTADA** |
| **Sistema Multi-Agente (Agentic AI)** | ✅ **IMPLEMENTADA** |
| **Dashboard de Bienestar (SQLite)** | ✅ **IMPLEMENTADA** |
| **Planificador Inteligente (IA)** | ✅ **IMPLEMENTADA** |
| Chat con Gemini | ✅ Funcional |
| Clasificación de riesgo con BETO | ✅ Funcional (como adapter) |
| Protocolo de crisis (CrisisOverlay) | ✅ Funcional |
| Popup de video (nivel Moderado) | ✅ Funcional |
| Registro de ánimo (backend) | ✅ Persistencia completa con SQLite (6 endpoints `/mood/*`) |
| Insights automáticos (backend) | ✅ Análisis de patrones y recomendaciones |
| Interfaz de Registro de ánimo (frontend) | ✅ `MoodLogPage.jsx` conectada a los 6 endpoints de `/mood` |
| Gestión de tareas (backend) | ✅ CRUD completo con priorización por IA |
| Análisis de agenda (backend) | ✅ Sugerencias inteligentes con Gemini |
| Interfaz del Planificador (frontend) | ✅ `TaskPlannerPage.jsx` conectado a los 10 endpoints de `/tasks` |
| Recursos por distrito | ✅ Funcional (SJL, Comas, Lima Centro) |
| Docker + despliegue en nube | ✅ Backend en Hugging Face Spaces, frontend en GitHub Pages, CI con GitHub Actions |
| Autenticación de usuarios | ⏳ Pendiente |

### Funcionalidades Implementadas (3/3 requeridas) ✅

#### ✅ Funcionalidad 1: Chat de Apoyo Emocional
- **Core:** Modelos (RiskAssessment, ChatResponse, Message) + Agent (base)
- **Ports:** 5 contratos (ChatServicePort + 4 outbound: Risk, LLM, Video, RAG)
- **Adapters:** BETOAdapter, GeminiAdapter, VideoRecommenderAdapter, RAGAdapter
- **Use Cases:** ProcessConversationWithAgentsUseCase
- **RAG:** ChromaDB + LangChain + 3 documentos FISI-UNSM
- **Agentes:** Sistema multi-agente (Coordinador + 3 agentes especializados)
- **Frontend:** `ChatPage.jsx` + `CrisisOverlay.jsx` + `VideoPopup.jsx`

#### ✅ Funcionalidad 2: Dashboard de Bienestar
- **Core:** Modelos (MoodEntry, MoodStatistics, MoodLevel)
- **Ports:** MoodLogRepositoryPort
- **Adapters:** SQLiteMoodLogRepository (persistencia en fisiagent.db)
- **Use Cases:** 6 casos de uso (Register, GetHistory, GetCalendar, GetInsights, Update, Delete)
- **API:** 6 endpoints REST completos
- **Insights:** Algoritmos de análisis de patrones y recomendaciones automáticas
- **Base de datos:** SQLite con índices optimizados
- **Frontend:** `MoodLogPage.jsx` (calendario, gráficos e insights) conectado a `/mood/history`, `/mood/insights`, `/mood/register`, `/mood/{id}` (update/delete); funciones cliente en `services/api.js`. El registro/edición solo permite el día actual o días con un registro existente, ya que el backend no soporta crear entradas retroactivas con fecha arbitraria.

#### ✅ Funcionalidad 3: Planificador Inteligente
- **Core:** Modelos (Task, TaskPriority, TaskStatus, TaskStatistics, DailySchedule)
- **Ports:** TaskRepositoryPort
- **Adapters:** SQLiteTaskRepository (tablas tasks + reminders)
- **Agente IA:** PlannerAgent (priorización inteligente con Gemini)
- **Use Cases:** 10 casos de uso (Create, Update, Complete, Delete, GetUpcoming, GetOverdue, Statistics, AnalyzeSchedule, GetSuggestions, CreateReminder)
- **API:** 10 endpoints REST con DTOs
- **IA Features:** 
  - Sugerencia automática de prioridad al crear tareas
  - Análisis de carga diaria con recomendaciones
  - Diagnóstico y sugerencias de organización general
- **Urgency Score:** Algoritmo que combina prioridad + proximidad de fecha límite
- **Frontend:** `TaskPlannerPage.jsx` (lista de tareas, formulario con sugerencia de IA, estadísticas, análisis de agenda y sugerencias de organización), funciones cliente en `services/api.js`
