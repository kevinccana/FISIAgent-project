# Sistema Implementado - FISIAgent

## ✅ Implementación Completa: RAG + Agentic AI

### 📦 Componentes Implementados

#### 1. RAG (Retrieval-Augmented Generation) - 🟠 Early Adopters
**Ubicación:** `app/adapters/outbound/rag_adapter.py`

**Tecnologías:**
- ChromaDB: Base de datos vectorial
- LangChain: Pipeline de carga y procesamiento
- sentence-transformers: Modelo `paraphrase-multilingual-MiniLM-L12-v2` (español)

**Documentos FISI-UNSM cargados:**
- `app/docs/fisi/reglamento_bienestar.txt` - Servicios de bienestar, protocolos de crisis
- `app/docs/fisi/faq_estudiantes.txt` - Preguntas frecuentes académicas
- `app/docs/fisi/plan_estudios.txt` - Plan de estudios completo (10 ciclos)

**Flujo:**
1. Carga documentos .txt del directorio `app/docs/fisi/`
2. Divide en chunks de 500 caracteres (overlap 50)
3. Genera embeddings con modelo multilingüe
4. Almacena en ChromaDB (persistido en `chroma_db/`)
5. Similarity search para recuperar top 3 chunks relevantes

---

#### 2. Sistema Multi-Agente - 🔴 Innovators
**Arquitectura:** Supervisor Pattern (Coordinador + Agentes Especializados)

**Agentes Implementados:**

##### CoordinadorAgente (`coordinator_agent.py`)
- Rol: Orquestador principal
- Responsabilidades:
  - Analiza el mensaje del usuario
  - Decide qué agentes invocar (heurísticas basadas en keywords)
  - Ejecuta pipeline: Risk → RAG (si aplica) → Empathy
  - Pasa contexto acumulado entre agentes

##### RiskAnalyzerAgent (`risk_analyzer_agent.py`)
- Rol: Clasificación de riesgo psicosocial
- Tecnología: BETO (BERT español) via `RiskClassifierPort`
- Salida: `RiskAssessment` (nivel + probabilidades)

##### RAGRetrieverAgent (`rag_retriever_agent.py`)
- Rol: Recuperación de información contextual
- Tecnología: ChromaDB via `RAGServicePort`
- Salida: `List[DocumentChunk]` (top 3 relevantes)
- Heurística activación: Keywords académicas (crédito, curso, beca, etc.)

##### EmpathyResponderAgent (`empathy_responder_agent.py`)
- Rol: Generación de respuesta empática final
- Tecnología: Gemini 2.5 Flash via `LLMServicePort`
- Funcionalidades:
  - Incorpora contexto RAG en system instruction si está disponible
  - Recomienda video si riesgo es Moderado
  - Respuesta de fallback si LLM falla
- Salida: `ChatResponse` completo

---

### 🏗️ Arquitectura Hexagonal

**Estructura:**
```
app/
├── core/
│   ├── domain/
│   │   ├── models.py         # Entidades (RiskAssessment, ChatResponse, etc.)
│   │   ├── exceptions.py     # Excepciones del dominio
│   │   └── agent.py          # Base: Agent, AgentRole, AgentTask, AgentResult
│   ├── use_cases/
│   │   ├── process_conversation.py              # [Legacy] Sin agentes
│   │   └── process_conversation_with_agents.py  # ✅ Con sistema multi-agente
│   └── agents/
│       ├── coordinator_agent.py
│       ├── risk_analyzer_agent.py
│       ├── rag_retriever_agent.py
│       └── empathy_responder_agent.py
├── ports/
│   ├── inbound/
│   │   └── chat_service.py   # ChatServicePort
│   └── outbound/
│       ├── risk_classifier.py      # RiskClassifierPort
│       ├── llm_service.py          # LLMServicePort
│       ├── video_recommender.py    # VideoRecommenderPort
│       └── rag_service.py          # ✅ RAGServicePort (nuevo)
└── adapters/
    ├── inbound/api/
    │   └── chat_router.py
    └── outbound/
        ├── beto_adapter.py
        ├── gemini_adapter.py
        ├── video_recommender_adapter.py
        └── rag_adapter.py              # ✅ Nuevo
```

---

### 🚀 Bootstrap en main.py

**Orden de inicialización:**

1. **Adapters Outbound (Infraestructura)**
   - BETOAdapter (clasificador)
   - GeminiAdapter (LLM)
   - RAGAdapter (vectorstore) ← **NUEVO**
   - VideoRecommenderAdapter

2. **Carga de Modelos**
   - BETO: Carga pesos desde `BETO_model/`
   - RAG: Carga documentos desde `app/docs/fisi/` → ChromaDB ← **NUEVO**

3. **Sistema Multi-Agente** ← **NUEVO**
   - Instancia agentes especializados (3)
   - Crea CoordinadorAgente con los agentes
   - Inyección de dependencias completa

4. **Use Case**
   - `ProcessConversationWithAgentsUseCase` con coordinador ← **NUEVO**

5. **API Router**
   - Configura endpoint `POST /chatai` con el nuevo use case

---

### 📊 Tendencias InfoQ 2025 Aplicadas

| Grupo | Tendencia | Implementación | Estado |
|-------|-----------|----------------|--------|
| 🔴 Innovators | **Agentic AI** | Sistema multi-agente con coordinador | ✅ |
| 🟠 Early Adopters | **RAG** | ChromaDB + LangChain + sentence-transformers | ✅ |
| 🟡 Early Majority | **AI-assisted development** | GitHub Copilot | ✅ |
| 🟢 Late Majority | **LLMs** | Gemini 2.5 Flash | ✅ |

---

### 🔄 Flujo de Ejecución Completo

**Ejemplo: Usuario pregunta "¿Cuántos créditos mínimos debo llevar?"**

1. **API Router** recibe request en `POST /chatai`
2. **Use Case** crea `AgentTask` para el coordinador
3. **CoordinadorAgente** analiza mensaje:
   - Detecta keyword "créditos" → activa RAG
   - Plan: `[RiskAnalyzerAgent, RAGRetrieverAgent, EmpathyResponderAgent]`
4. **RiskAnalyzerAgent** ejecuta:
   - Llama `BETOAdapter.classify()`
   - Resultado: `RiskLevel.CONTROL, probabilidades={...}`
5. **RAGRetrieverAgent** ejecuta:
   - Llama `RAGAdapter.retrieve_context("¿Cuántos créditos mínimos...?")`
   - ChromaDB similarity search
   - Resultado: `[chunk1, chunk2, chunk3]` (de plan_estudios.txt)
6. **EmpathyResponderAgent** ejecuta:
   - Construye system instruction con contexto RAG
   - Llama `GeminiAdapter.generate_response()`
   - Resultado: Respuesta empática + datos del plan de estudios
7. **Use Case** retorna `ChatResponse` completo
8. **API Router** serializa a JSON

---

### 📝 Próximos Pasos Recomendados

#### Para completar la Funcionalidad 1 (Chat de Apoyo Emocional):
- [ ] Instalar dependencias: `pip install -r requirements.txt`
- [ ] Verificar que ChromaDB crea `chroma_db/` en startup
- [ ] Probar con preguntas académicas:
  - "¿Hay psicólogo en la universidad?"
  - "¿Puedo retirarme de un curso?"
  - "¿Cuántos créditos mínimos debo llevar?"
- [ ] Probar con preguntas emocionales (sin RAG)
- [ ] Verificar logs: `[Startup] ✓ RAG inicializado correctamente`

#### Para Funcionalidad 2 (Dashboard de Bienestar):
- [ ] Crear base de datos SQLite para registros de ánimo
- [ ] Implementar endpoints CRUD para mood logs
- [ ] Crear agente analítico para insights (opcional)

#### Para Funcionalidad 3 (Planificador Inteligente):
- [ ] Definir estructura de tareas/recordatorios
- [ ] Implementar agente planificador con Google Calendar API
- [ ] Crear endpoints de gestión de tareas

#### Despliegue:
- [ ] Crear Dockerfile multi-stage (Python 3.10 + FastAPI)
- [ ] Configurar Railway/Render con persistencia para `chroma_db/`
- [ ] Variables de entorno: `GEMINI_API_KEY`

---

### 🐛 Troubleshooting

**Si RAG no carga:**
```
[Startup] ⚠ RAG no disponible
```
- Verificar que existe `app/docs/fisi/` con archivos .txt
- Instalar: `pip install langchain chromadb sentence-transformers`

**Si ChromaDB da error de permisos:**
- Verificar permisos de escritura en directorio `chroma_db/`
- En Windows: ejecutar como administrador la primera vez

**Si agentes no responden:**
- Verificar logs: `logger.info()` en cada agente
- Activar `exc_info=True` en `logger.error()` para stack traces
