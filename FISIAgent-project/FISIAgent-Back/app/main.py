"""
app/main.py
===========
Punto de entrada de la API FastAPI de FISIAgent.

Startup:
  Al arrancar el servidor se carga el modelo BETO en memoria (ver cargar_modelo).
  Esto toma ~2-4 s una sola vez y deja el modelo listo para todas las peticiones.
  Si la carga falla, el servicio continúa en modo fallback (palabras clave).
"""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes import chat, health, gemini
from app.services.nlp import cargar_modelo

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Carga el modelo BETO al iniciar y libera recursos al apagar."""
    logger.info("[Startup] Cargando modelo BETO...")
    exito = cargar_modelo()
    if exito:
        logger.info("[Startup] BETO listo. Clasificación de riesgo activa.")
    else:
        logger.warning("[Startup] BETO no disponible. Usando detección por palabras clave.")
    yield
    logger.info("[Shutdown] Servidor apagado.")


app = FastAPI(
    title="FISIAgent API",
    version="1.0.0",
    lifespan=lifespan,
)

# ── CORS ───────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ────────────────────────────────────────────────────────────────────
app.include_router(chat.router)
app.include_router(health.router)
app.include_router(gemini.router)


@app.get("/")
def root():
    return {"message": "API funcionando 🚀"}