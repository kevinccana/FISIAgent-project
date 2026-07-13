# app/routes/gemini.py
"""
Endpoint /chatai — Chat con IA y clasificación de riesgo psicosocial.

Responsabilidades de cada componente:
  - BETO (app/services/nlp.py) : clasifica el nivel de riesgo del mensaje
                                  del usuario (Control / Moderado / Crítico).
  - Gemini 2.5 Flash            : genera la respuesta empática en lenguaje natural.

El endpoint ejecuta ambas tareas y devuelve:
  - respuesta      : texto generado por Gemini.
  - nivel_riesgo   : nivel detectado por BETO ("control" | "moderado" | "critico").
  - video_sugerido : info del video recomendado si nivel == "moderado", sino null.
  - probabilidades : probabilidades por clase de BETO (útil para debug/logging).
"""
import os
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List
from dotenv import load_dotenv

load_dotenv()

from google import genai
from google.genai import types
from app.services.nlp import clasificar_riesgo, VIDEOS_AYUDA

# ── Router ─────────────────────────────────────────────────────────────────────
router = APIRouter()

# ── Modelos Pydantic ───────────────────────────────────────────────────────────
class ChatMessage(BaseModel):
    role: str  # "user" | "model"
    text: str

class ChatRequest(BaseModel):
    history: List[ChatMessage]

# ── System Instruction para Gemini ────────────────────────────────────────────
SYSTEM_INSTRUCTION = """
Eres un asistente de apoyo psicológico empático, cálido y profesional.
Tu objetivo es escuchar activamente, validar emociones y ofrecer estrategias de afrontamiento básicas.

REGLAS CRÍTICAS:
1. No eres un psicólogo real ni puedes dar diagnósticos médicos.
2. Si el usuario te pregunta sobre temas irrelevantes (cocina, programación, chistes, etc.),
   rechaza la pregunta amablemente indicando que tu función es solo el apoyo emocional.
3. Si detectas ideas de suicidio o autolesión, activa el protocolo de crisis:
   muestra empatía profunda y proporciona líneas de ayuda o números de emergencia de inmediato.
"""

# ── Selección de video con Gemini ─────────────────────────────────────────────
def seleccionar_video_con_gemini(texto: str, client) -> dict:
    """
    Usa Gemini para elegir el video más apropiado del catálogo según el mensaje.

    Envía a Gemini el mensaje del usuario y la lista de videos con sus situaciones.
    Gemini responde con el 'tipo' del video más adecuado (ej: "respiracion").
    Si Gemini falla, retorna el video de mindfulness como fallback.
    """
    catalogo_str = "\n".join(
        f"- tipo: {v['tipo']} | situacion: {v['situacion']}"
        for v in VIDEOS_AYUDA
    )

    prompt = (
        f"Un usuario escribió: \"{texto}\"\n\n"
        f"Elige el tipo de video de apoyo más apropiado para su situación.\n"
        f"Opciones disponibles:\n{catalogo_str}\n\n"
        f"Responde ÚNICAMENTE con el valor del campo 'tipo', sin explicación. "
        f"Ejemplo de respuesta válida: respiracion"
    )

    try:
        respuesta = client.models.generate_content(
            model="gemini-3.1-flash-lite",
            contents=prompt,
            config=types.GenerateContentConfig(temperature=0.1),
        )
        tipo_elegido = respuesta.text.strip().lower().replace(".", "")

        video = next((v for v in VIDEOS_AYUDA if v["tipo"] == tipo_elegido), None)
        return video if video else VIDEOS_AYUDA[1]  # fallback: mindfulness

    except Exception:
        return VIDEOS_AYUDA[1]  # fallback: mindfulness


# ── Endpoint ───────────────────────────────────────────────────────────────────
@router.post("/chatai")
async def chat_endpoint(request: ChatRequest):
    """
    Procesa un mensaje de chat aplicando dos capas de análisis en paralelo:

    1. Clasificación de riesgo (BETO):
       - Extrae el último mensaje del usuario del historial.
       - Llama a clasificar_riesgo() para obtener nivel y video sugerido.
       - No bloquea ni modifica la respuesta de Gemini.

    2. Respuesta empática (Gemini 2.5 Flash):
       - Recibe el historial completo de la conversación.
       - Genera una respuesta contextualizada según el system instruction.

    El frontend usa nivel_riesgo para decidir qué mostrar:
      "control"  → solo muestra la respuesta en el chat.
      "moderado" → muestra la respuesta + VideoPopup con video_sugerido.
      "critico"  → muestra la respuesta + CrisisOverlay.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise HTTPException(
            status_code=500,
            detail="Error de configuración: GEMINI_API_KEY no encontrada en el servidor.",
        )

    # ── 1. BETO: clasificación de riesgo (siempre se ejecuta) ─────────────────
    # Se ejecuta fuera del try/except de Gemini para que el nivel de riesgo
    # siempre llegue al frontend, incluso si Gemini falla por rate limit (429).
    ultimo_mensaje = next(
        (msg.text for msg in reversed(request.history) if msg.role == "user"),
        "",
    )
    riesgo = clasificar_riesgo(ultimo_mensaje)

    # ── 2. Gemini: respuesta empática + selección de video ────────────────────
    client = genai.Client(api_key=api_key)

    try:
        contents = [
            types.Content(
                role=msg.role,
                parts=[types.Part.from_text(text=msg.text)],
            )
            for msg in request.history
        ]

        config = types.GenerateContentConfig(
            system_instruction=SYSTEM_INSTRUCTION,
            temperature=0.7,
        )

        response = client.models.generate_content(
            model="gemini-3.1-flash-lite",
            contents=contents,
            config=config,
        )
        texto_respuesta = response.text

    except Exception:
        # Si Gemini falla (429, timeout, etc.), se devuelve igual el nivel de BETO
        # para que el frontend active CrisisOverlay o VideoPopup correctamente.
        texto_respuesta = (
            "Estoy aquí para ti. En este momento tengo dificultades técnicas, "
            "pero lo más importante es que no estás solo/a."
        )

    # ── 3. Selección de video con Gemini (solo si nivel moderado) ─────────────
    video_sugerido = None
    if riesgo["nivel"] == "moderado":
        video_sugerido = seleccionar_video_con_gemini(ultimo_mensaje, client)

    # ── 4. Respuesta unificada ────────────────────────────────────────────────
    return {
        "respuesta"     : texto_respuesta,
        "nivel_riesgo"  : riesgo["nivel"],
        "video_sugerido": video_sugerido,
        "probabilidades": riesgo["probabilidades"],
    }
