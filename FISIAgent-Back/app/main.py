"""
app/main.py
===========
Punto de entrada de la API FastAPI de FISIAgent.

ARQUITECTURA HEXAGONAL:
  - Core: Lógica de negocio en app/core/
  - Ports: Contratos/interfaces en app/ports/
  - Adapters: Implementaciones concretas en app/adapters/

Startup:
  1. Se cargan los adapters outbound (BETO, Gemini)
  2. Se inicializa el caso de uso con los adapters
  3. Se configura el adapter inbound (FastAPI router)
"""
import logging
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# ── Arquitectura Hexagonal ─────────────────────────────────────────────────────
from app.adapters.outbound.beto_adapter import BETOAdapter
from app.adapters.outbound.gemini_adapter import GeminiAdapter
from app.adapters.outbound.video_recommender_adapter import VideoRecommenderAdapter
from app.adapters.outbound.rag_adapter import RAGAdapter
from app.adapters.outbound.sqlite_mood_repository import SQLiteMoodLogRepository
from app.adapters.outbound.sqlite_task_repository import SQLiteTaskRepository
from app.core.use_cases.process_conversation import ProcessConversationUseCase
from app.core.use_cases.process_conversation_with_agents import ProcessConversationWithAgentsUseCase
from app.core.use_cases.mood_use_cases import (
    RegisterMoodUseCase,
    GetMoodHistoryUseCase,
    GetMonthlyCalendarUseCase,
    GetMoodInsightsUseCase,
    GetMoodAIInsightsUseCase,
    UpdateMoodUseCase,
    DeleteMoodUseCase
)
from app.core.use_cases.task_use_cases import (
    CreateTaskUseCase,
    GetUpcomingTasksUseCase,
    GetOverdueTasksUseCase,
    UpdateTaskUseCase,
    CompleteTaskUseCase,
    DeleteTaskUseCase,
    GetTaskStatisticsUseCase,
    AnalyzeDailyScheduleUseCase,
    GetTaskOrganizationSuggestionsUseCase,
    CreateReminderUseCase
)
from app.core.domain.agent import AgentRole
from app.core.agents import (
    CoordinadorAgente,
    RiskAnalyzerAgent,
    RAGRetrieverAgent,
    EmpathyResponderAgent
)
from app.core.agents.planner_agent import PlannerAgent
from app.core.agents.mood_insights_agent import MoodInsightsAgent
from app.adapters.inbound.api import chat_router
from app.adapters.inbound.api import mood_router
from app.adapters.inbound.api import task_router
from app.adapters.inbound.api import dev_router

# ── Rutas legacy (compatibilidad) ──────────────────────────────────────────────
from app.routes import chat, health, gemini

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Inicializa la aplicación con Arquitectura Hexagonal + Agentic AI + RAG.
    
    1. Instancia los adapters outbound (BETO, Gemini, RAG, VideoRecommender)
    2. Carga modelos (BETO + RAG con ChromaDB)
    3. Crea agentes especializados (Risk, RAG, Empathy)
    4. Crea coordinador multi-agente
    5. Crea el caso de uso con inyección de dependencias
    6. Configura el adapter inbound (API router)
    """
    logger.info("[Startup] Inicializando FISIAgent - Hexagonal + Agentic AI + RAG...")
    
    # ═══════════════════════════════════════════════════════════════════════════
    # 1. Outbound Adapters (Infraestructura)
    # ═══════════════════════════════════════════════════════════════════════════
    
    # 1.1 BETO Adapter (Clasificación de riesgo)
    beto_adapter = BETOAdapter()
    
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        logger.warning("[Startup] ⚠ GEMINI_API_KEY no encontrada")
    
    # 1.2 Gemini Adapter (LLM)
    gemini_adapter = GeminiAdapter(api_key=api_key or "")

    # Se guardan en app.state para que el endpoint GET /status (visualizador del
    # chatbot: ¿BETO cargó?, ¿la API key de Gemini responde?) los pueda leer.
    app.state.beto_adapter = beto_adapter
    app.state.gemini_adapter = gemini_adapter

    # 1.3 RAG Adapter (Early Adopters - InfoQ 2025)
    # ENABLE_RAG=false en entornos con RAM limitada (ej. Render free tier, 512MB no
    # alcanza para BETO + el modelo de embeddings de RAG a la vez). Por defecto activo.
    rag_enabled = os.getenv("ENABLE_RAG", "true").strip().lower() != "false"
    app.state.rag_enabled = rag_enabled
    logger.info(f"[Startup] Inicializando RAG con ChromaDB... (enabled={rag_enabled})")
    rag_adapter = RAGAdapter(
        docs_path="app/docs/fisi",
        persist_directory="chroma_db",
        enabled=rag_enabled
    )
    
    # 1.4 Video Recommender
    try:
        from google import genai
        gemini_client = genai.Client(api_key=api_key)
        video_recommender = VideoRecommenderAdapter(llm_client=gemini_client)
        logger.info("[Startup] ✓ Video recommender inicializado")
    except Exception as e:
        logger.error(f"[Startup] Error al inicializar video recommender: {e}")
        video_recommender = None
    
    # ═══════════════════════════════════════════════════════════════════════════
    # 2. Carga de modelos
    # ═══════════════════════════════════════════════════════════════════════════
    
    # 2.1 Cargar BETO
    logger.info("[Startup] Cargando modelo BETO...")
    exito_beto = beto_adapter.load_model()
    if exito_beto:
        logger.info("[Startup] ✓ BETO cargado correctamente")
    else:
        logger.warning("[Startup] ⚠ BETO no disponible, usando fallback")
    
    # 2.2 Cargar documentos RAG
    logger.info("[Startup] Cargando documentos FISI-UNSM para RAG...")
    try:
        rag_adapter.load_documents()
        if rag_adapter.is_available():
            logger.info("[Startup] ✓ RAG inicializado correctamente")
        else:
            logger.warning("[Startup] ⚠ RAG no disponible")
    except Exception as e:
        logger.error(f"[Startup] Error al cargar RAG: {e}")
    
    # ═══════════════════════════════════════════════════════════════════════════
    # 3. Sistema Multi-Agente (Innovators - InfoQ 2025)
    # ═══════════════════════════════════════════════════════════════════════════
    
    logger.info("[Startup] Creando sistema multi-agente...")
    
    # 3.1 Agentes especializados
    risk_agent = RiskAnalyzerAgent(risk_classifier=beto_adapter)
    rag_agent = RAGRetrieverAgent(rag_service=rag_adapter)
    empathy_agent = EmpathyResponderAgent(
        llm_service=gemini_adapter,
        video_recommender=video_recommender
    )
    
    # 3.2 Coordinador (Supervisor)
    coordinador = CoordinadorAgente(agents={
        AgentRole.RISK_ANALYZER: risk_agent,
        AgentRole.RAG_RETRIEVER: rag_agent,
        AgentRole.EMPATHY_RESPONDER: empathy_agent
    })
    logger.info("[Startup] ✓ Sistema multi-agente inicializado (3 agentes + coordinador)")
    
    # ═══════════════════════════════════════════════════════════════════════════
    # 4. Use Case (Lógica de negocio) con Agentic AI
    # ═══════════════════════════════════════════════════════════════════════════
    
    chat_use_case_agents = ProcessConversationWithAgentsUseCase(
        coordinator=coordinador
    )
    logger.info("[Startup] ✓ Caso de uso con agentes inicializado")
    
    # ═══════════════════════════════════════════════════════════════════════════
    # 5. Configurar adapter inbound (API)
    # ═══════════════════════════════════════════════════════════════════════════
    
    chat_router.set_chat_service(chat_use_case_agents)
    logger.info("[Startup] ✓ API router configurado con sistema de agentes")
    
    # ═══════════════════════════════════════════════════════════════════════════
    # 6. Dashboard de Bienestar (Mood Logs) - Funcionalidad 2
    # ═══════════════════════════════════════════════════════════════════════════
    
    logger.info("[Startup] Inicializando Dashboard de Bienestar...")
    
    # 6.1 Repositorio SQLite
    mood_repository = SQLiteMoodLogRepository(db_path="fisiagent.db")
    
    # 6.2 Agente de análisis elaborado (Gemini) -- opt-in, ver mood_insights_agent.py
    mood_insights_agent = MoodInsightsAgent(llm_service=gemini_adapter)

    # 6.3 Casos de uso
    register_mood_uc = RegisterMoodUseCase(mood_repository)
    get_history_uc = GetMoodHistoryUseCase(mood_repository)
    get_calendar_uc = GetMonthlyCalendarUseCase(mood_repository)
    get_insights_uc = GetMoodInsightsUseCase(mood_repository)
    get_ai_insights_uc = GetMoodAIInsightsUseCase(mood_repository, mood_insights_agent)
    update_mood_uc = UpdateMoodUseCase(mood_repository)
    delete_mood_uc = DeleteMoodUseCase(mood_repository)

    # 6.4 Configurar router
    mood_router.configure_mood_router(
        register_mood=register_mood_uc,
        get_history=get_history_uc,
        get_calendar=get_calendar_uc,
        get_insights=get_insights_uc,
        update_mood=update_mood_uc,
        delete_mood=delete_mood_uc,
        get_ai_insights=get_ai_insights_uc
    )
    logger.info("[Startup] ✓ Dashboard de Bienestar inicializado (SQLite)")
    
    # ═══════════════════════════════════════════════════════════════════════════
    # 7. Planificador Inteligente (Tasks) - Funcionalidad 3
    # ═══════════════════════════════════════════════════════════════════════════
    
    logger.info("[Startup] Inicializando Planificador Inteligente...")
    
    # 7.1 Repositorio SQLite
    task_repository = SQLiteTaskRepository(db_path="fisiagent.db")
    
    # 7.2 Agente de planificación con IA
    planner_agent = PlannerAgent(llm_service=gemini_adapter)
    logger.info("[Startup] ✓ PlannerAgent inicializado")
    
    # 7.3 Casos de uso
    create_task_uc = CreateTaskUseCase(task_repository, planner_agent)
    get_upcoming_tasks_uc = GetUpcomingTasksUseCase(task_repository)
    get_overdue_tasks_uc = GetOverdueTasksUseCase(task_repository)
    update_task_uc = UpdateTaskUseCase(task_repository)
    complete_task_uc = CompleteTaskUseCase(task_repository)
    delete_task_uc = DeleteTaskUseCase(task_repository)
    get_task_statistics_uc = GetTaskStatisticsUseCase(task_repository)
    analyze_schedule_uc = AnalyzeDailyScheduleUseCase(task_repository, planner_agent)
    get_suggestions_uc = GetTaskOrganizationSuggestionsUseCase(task_repository, planner_agent)
    create_reminder_uc = CreateReminderUseCase(task_repository)
    
    # 7.4 Configurar router
    task_router.configure_task_router(
        create_task=create_task_uc,
        get_upcoming=get_upcoming_tasks_uc,
        get_overdue=get_overdue_tasks_uc,
        update_task=update_task_uc,
        complete_task=complete_task_uc,
        delete_task=delete_task_uc,
        get_statistics=get_task_statistics_uc,
        analyze_schedule=analyze_schedule_uc,
        get_suggestions=get_suggestions_uc,
        create_reminder=create_reminder_uc
    )
    logger.info("[Startup] ✓ Planificador Inteligente inicializado (SQLite + IA)")
    
    logger.info("[Startup] 🚀 FISIAgent listo")
    logger.info("[Startup] 📊 Tendencias InfoQ 2025 implementadas:")
    logger.info("[Startup]    🔴 Innovators: Agentic AI (Multi-Agent + Planner)")
    logger.info("[Startup]    🟠 Early Adopters: RAG (ChromaDB + LangChain)")
    logger.info("[Startup]    🟡 Early Majority: AI-assisted development")
    logger.info("[Startup]    🟢 Late Majority: LLMs (Gemini 3.1 Flash Lite)")
    logger.info("[Startup] 📊 Funcionalidades:")
    logger.info("[Startup]    ✅ Funcionalidad 1: Chat de Apoyo Emocional (RAG + Agentes)")
    logger.info("[Startup]    ✅ Funcionalidad 2: Dashboard de Bienestar (SQLite)")
    logger.info("[Startup]    ✅ Funcionalidad 3: Planificador Inteligente (Tasks + IA)")
    
    yield
    
    logger.info("[Shutdown] Servidor apagado.")


app = FastAPI(
    title="FISIAgent API",
    version="3.0.0",
    lifespan=lifespan,
)

# ── CORS ───────────────────────────────────────────────────────────────────────
# FRONTEND_URL: orígenes adicionales permitidos en producción (ej. la URL de GitHub
# Pages), separados por coma. Los orígenes de desarrollo local siempre se permiten.
_dev_origins = ["http://localhost:5173", "http://127.0.0.1:5173"]
_prod_origins = [o.strip() for o in os.getenv("FRONTEND_URL", "").split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_dev_origins + _prod_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ────────────────────────────────────────────────────────────────────
# Routers principales (Arquitectura Hexagonal)
app.include_router(chat_router.router, tags=["Chat (Hexagonal)"])
app.include_router(mood_router.router, tags=["Dashboard de Bienestar"])
app.include_router(task_router.router, tags=["Planificador Inteligente"])
app.include_router(dev_router.router, tags=["Utilidades de desarrollo"])

# Routers legacy (compatibilidad con código existente)
app.include_router(chat.router, tags=["Legacy"])
app.include_router(health.router, tags=["Health"])
app.include_router(gemini.router, tags=["Legacy"])


@app.get("/")
def root():
    return {
        "message": "3.0.0",
        "architecture": "Hexagonal (Ports & Adapters)",
        "features": [
            "Chat de Apoyo Emocional (RAG + Agentic AI)",
            "Dashboard de Bienestar (Mood Logs con SQLite)",
            "Planificador Inteligente (Tasks con priorización por IA)"
        ],
        "info_q_trends": {
            "innovators": "Agentic AI (Multi-Agent System + Planner Agent)",
            "early_adopters": "RAG (ChromaDB + LangChain)",
            "early_majority": "AI-assisted development (GitHub Copilot)",
            "late_majority": "LLMs (Gemini 3.1 Flash Lite)"
        },
        "status": "running"
    }


@app.get("/status")
def status(request: Request):
    """
    Visualizador de estado para el chatbot: confirma si BETO cargó (o si está
    en modo fallback por palabras clave) y si la API key de Gemini responde de
    verdad (no solo si la variable de entorno existe -- una key inválida o sin
    cupo también se refleja acá).
    """
    beto_adapter = request.app.state.beto_adapter
    gemini_adapter = request.app.state.gemini_adapter
    gemini_status = gemini_adapter.check_connection()

    return {
        "beto": "active" if beto_adapter.is_available() else "fallback",
        "rag": "active" if request.app.state.rag_enabled else "disabled",
        "gemini": "ok" if gemini_status["ok"] else "error",
        "gemini_detail": gemini_status["detail"],
    }