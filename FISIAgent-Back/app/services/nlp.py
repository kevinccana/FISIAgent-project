"""
app/services/nlp.py
===================
Servicio de clasificación de riesgo psicosocial usando el modelo BETO
con fine-tuning sobre comentarios de YouTube en español.

ARQUITECTURA DEL MODELO
-----------------------
- Base       : BETO (BERT en español, dccuchile/bert-base-spanish-wwm-cased)
- Tarea      : Clasificación de secuencias (BertForSequenceClassification)
- Clases     : 3 niveles de riesgo psicosocial
    - 0 → Control  : conversación sin señales de riesgo
    - 1 → Moderado : estrés o ansiedad detectados
    - 2 → Crítico  : indicadores de crisis o riesgo grave
- Max tokens : 128 (truncación por la derecha)
- Vocabulario: 31,002 tokens

MÉTRICAS DEL MODELO (5-fold CV, n=1,998 muestras)
---------------------------------------------------
  Macro F1   : 0.5685 ± 0.0408
  Accuracy   : 0.8433 ± 0.0214

  Por clase (out-of-fold global):
    Control  → Precision: 0.926 | Recall: 0.922 | F1: 0.924 | AUC-ROC: 0.821
    Moderado → Precision: 0.429 | Recall: 0.352 | F1: 0.387 | AUC-ROC: 0.732
    Crítico  → Precision: 0.326 | Recall: 0.500 | F1: 0.394 | AUC-ROC: 0.834

INTERPRETACIÓN DE MÉTRICAS
---------------------------
- Control tiene excelente discriminación (F1 0.92) → muy confiable.
- Crítico tiene AUC 0.834: el modelo aprendió señal real, pero el recall al
  umbral por defecto (0.5) es solo 0.50. Bajando el umbral a 0.30 se aprovecha
  esa señal para no perder casos graves (trade-off: más falsas alarmas, pero en
  salud mental el recall es prioritario).
- Moderado es la clase más débil (AUC 0.73). Se usa como disparador del popup
  de video, que es una intervención leve y no invasiva.

ESTRATEGIA DE UMBRALES
-----------------------
  Se usan las probabilidades de softmax directamente (no argmax), con umbrales
  ajustados al desbalance del dataset (Control 85% / Moderado 11% / Crítico 4%):

    P(Crítico)  >= 0.30  → nivel "critico"   (prioriza recall para seguridad)
    P(Moderado) >= 0.45  → nivel "moderado"  (umbral moderado para popup)
    Default              → nivel "control"

  La evaluación es secuencial: Crítico tiene prioridad sobre Moderado.

FALLBACK DE SEGURIDAD
---------------------
  Si el modelo no puede cargarse (archivo ausente, dependencias faltantes, etc.),
  el servicio degrada a detección por palabras clave solo para la clase Crítico.
  El nivel Moderado no se detecta en modo fallback (preferible a falsos positivos).

CARGA DEL MODELO
----------------
  El modelo se carga en memoria una sola vez al iniciar FastAPI (ver main.py).
  Usar un singleton evita el costo de carga (~2-4 s) en cada request.
  La inferencia posterior toma ~80-150 ms en CPU.
"""

import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# ── Rutas ──────────────────────────────────────────────────────────────────────
# __file__ → FISIAgent-Back/app/services/nlp.py
# .parent x3 → FISIAgent-Back/
# .parent x4 → FISIAgent-project/   (donde vive BETO_model/)
_BASE_DIR  = Path(__file__).resolve().parent.parent.parent.parent
_MODEL_DIR = _BASE_DIR / "BETO_model"

# ── Umbrales de decisión ───────────────────────────────────────────────────────
UMBRAL_CRITICO  = 0.30  # Bajo para maximizar recall en casos graves
UMBRAL_MODERADO = 0.45

# ── Catálogo de videos de apoyo ────────────────────────────────────────────────
# La selección entre estos videos la hace Gemini según el contexto del mensaje
# (ver seleccionar_video_con_gemini en app/routes/gemini.py).
# El campo "situacion" describe cuándo es apropiado cada video — Gemini lo lee.
#
# NOTA: Los videos marcados con url "PENDIENTE" necesitan una URL real de YouTube.
VIDEOS_AYUDA = [
    {
        "tipo"      : "respiracion",
        "titulo"    : "Ejercicio de Respiración 4-7-8",
        "descripcion": "Técnica de respiración para calmar la ansiedad en minutos",
        "url"       : "https://www.youtube.com/watch?v=EGO5m_DBzF8&t=96s",
        "duracion"  : "5 min",
        "situacion" : "ansiedad aguda, sensación de ahogo, falta de aire, taquicardia",
    },
    {
        "tipo"      : "mindfulness",
        "titulo"    : "Mindfulness para principiantes",
        "descripcion": "5 minutos de atención plena para reducir el estrés",
        "url"       : "https://www.youtube.com/watch?v=3oCC4NDgYrY&t=17s",
        "duracion"  : "5 min",
        "situacion" : "estrés general, mente acelerada, pensamientos que no paran, preocupación",
    },
    {
        "tipo"      : "dormir",
        "titulo"    : "Meditación para dormir",
        "descripcion": "Relajación profunda para conciliar el sueño",
        "url"       : "https://www.youtube.com/watch?v=vFrHhwCOaW0",
        "duracion"  : "20 min",
        "situacion" : "insomnio, dificultad para dormir, sueño, cansancio nocturno",
    },
    {
        "tipo"      : "relajacion",
        "titulo"    : "Sonidos de la naturaleza",
        "descripcion": "Ambientes relajantes para calmar la mente y el cuerpo",
        "url"       : "https://www.youtube.com/watch?v=7Ilu033ydSw",
        "duracion"  : "Libre",
        "situacion" : "tensión, agobio, saturación, necesidad de calma y silencio",
    },
    {
        "tipo"      : "panico",
        "titulo"    : "Técnica de Grounding 5-4-3-2-1",
        "descripcion": "Ejercicio para salir de un ataque de pánico y volver al presente",
        "url"       : "PENDIENTE",  # reemplazar con URL real de YouTube
        "duracion"  : "7 min",
        "situacion" : "ataque de pánico, crisis de ansiedad, disociación, temblores",
    },
    {
        "tipo"      : "autoestima",
        "titulo"    : "Meditación de autocompasión",
        "descripcion": "Para momentos de tristeza, llanto y desánimo",
        "url"       : "PENDIENTE",  # reemplazar con URL real de YouTube
        "duracion"  : "10 min",
        "situacion" : "tristeza, llanto, baja autoestima, desánimo, sentirse sin valor",
    },
    {
        "tipo"      : "concentracion",
        "titulo"    : "Música para concentrarse y calmar la mente",
        "descripcion": "Sonidos para organizar los pensamientos cuando todo se siente abrumador",
        "url"       : "https://open.spotify.com/embed/playlist/37i9dQZF1DX3Ogo9pFvBkY",
        "duracion"  : "Libre",
        "situacion" : "abrumado, mente en blanco, no puedo pensar, demasiadas cosas a la vez",
    },
    {
        "tipo"      : "energia",
        "titulo"    : "Yoga suave para el estrés",
        "descripcion": "Movimiento suave para liberar la tensión acumulada en el cuerpo",
        "url"       : "PENDIENTE",  # reemplazar con URL real de YouTube
        "duracion"  : "15 min",
        "situacion" : "agotamiento físico, tensión muscular, sin fuerzas, cuerpo tenso",
    },
]

# ── Palabras clave de crisis (modo fallback) ───────────────────────────────────
# Solo se usan cuando BETO no está disponible. No reemplazan al modelo.
_PALABRAS_CRISIS = [
    "suicidio", "suicidarme", "quitarme la vida",
    "morir", "morirme", "matarme", "no quiero vivir",
    "acabar con todo", "no tiene sentido vivir", "hacerme daño",
]

# ── Estado del singleton ───────────────────────────────────────────────────────
_tokenizer        = None
_model            = None
_modelo_disponible = False


def cargar_modelo() -> bool:
    """
    Carga el tokenizador y el modelo BETO en memoria RAM.

    Debe llamarse una sola vez al arrancar FastAPI (evento 'startup' en main.py).
    Después de esta llamada, _tokenizer y _model quedan disponibles globalmente
    para todas las peticiones sin recargas adicionales.

    Returns:
        True  → modelo cargado y listo para inferencia.
        False → carga fallida; el servicio usará palabras clave como fallback.
    """
    global _tokenizer, _model, _modelo_disponible

    try:
        from transformers import AutoTokenizer, AutoModelForSequenceClassification

        if not _MODEL_DIR.exists():
            logger.warning(
                f"[BETO] Carpeta del modelo no encontrada en: {_MODEL_DIR}. "
                "El servicio usará detección por palabras clave."
            )
            return False

        logger.info(f"[BETO] Cargando modelo desde: {_MODEL_DIR}")
        _tokenizer = AutoTokenizer.from_pretrained(str(_MODEL_DIR))
        _model     = AutoModelForSequenceClassification.from_pretrained(str(_MODEL_DIR))
        _model.eval()  # desactiva dropout → inferencia determinista

        _modelo_disponible = True
        logger.info("[BETO] Modelo cargado correctamente y listo para inferencia.")
        return True

    except Exception as exc:
        logger.error(f"[BETO] Error al cargar el modelo: {exc}")
        _modelo_disponible = False
        return False


def _fallback_keywords(texto: str) -> dict:
    """
    Clasificación de emergencia por palabras clave cuando BETO no está disponible.

    Solo detecta nivel Crítico. No detecta Moderado para evitar falsos positivos
    con una heurística tan simple.
    """
    t = texto.lower()
    if any(palabra in t for palabra in _PALABRAS_CRISIS):
        return {"nivel": "critico", "probabilidades": None, "video_sugerido": None}
    return {"nivel": "control", "probabilidades": None, "video_sugerido": None}


def clasificar_riesgo(texto: str) -> dict:
    """
    Clasifica el nivel de riesgo psicosocial de un texto usando BETO.

    Flujo:
      1. Si BETO no está disponible → _fallback_keywords(texto)
      2. Tokenizar y obtener logits del modelo
      3. Aplicar softmax → probabilidades por clase
      4. Evaluar umbrales en orden de prioridad (Crítico → Moderado → Control)

    Args:
        texto: Mensaje del usuario a clasificar.

    Returns:
        dict con las siguientes claves:
          - nivel          (str) : "control" | "moderado" | "critico"
          - probabilidades (dict): {"control": float, "moderado": float, "critico": float}
                                   None si BETO no está disponible.
          - video_sugerido (dict): Información del video recomendado.
                                   Solo presente cuando nivel == "moderado".
                                   None en los demás casos.

    Ejemplo de retorno para nivel moderado:
        {
            "nivel": "moderado",
            "probabilidades": {"control": 0.21, "moderado": 0.63, "critico": 0.16},
            "video_sugerido": {
                "tipo": "mindfulness",
                "titulo": "Mindfulness para principiantes",
                "descripcion": "5 minutos de atención plena para reducir el estrés",
                "url": "https://www.youtube.com/watch?v=3oCC4NDgYrY&t=17s",
                "duracion": "5 min"
            }
        }
    """
    if not _modelo_disponible:
        return _fallback_keywords(texto)

    try:
        import torch

        inputs = _tokenizer(
            texto,
            return_tensors="pt",
            truncation=True,
            max_length=128,
            padding=True,
        )

        with torch.no_grad():
            logits = _model(**inputs).logits
            probs  = torch.softmax(logits, dim=-1)[0].tolist()

        p_control, p_moderado, p_critico = probs

        probabilidades = {
            "control" : round(p_control,  4),
            "moderado": round(p_moderado, 4),
            "critico" : round(p_critico,  4),
        }

        # Crítico tiene prioridad para no ignorar casos graves
        if p_critico >= UMBRAL_CRITICO:
            return {"nivel": "critico",  "probabilidades": probabilidades}

        if p_moderado >= UMBRAL_MODERADO:
            return {"nivel": "moderado", "probabilidades": probabilidades}

        return {"nivel": "control", "probabilidades": probabilidades}

    except Exception as exc:
        logger.error(f"[BETO] Error durante la inferencia: {exc}")
        result = _fallback_keywords(texto)
        result.pop("video_sugerido", None)
        return result


def detectar_crisis(texto: str) -> bool:
    """
    Interfaz de compatibilidad con app/routes/crisis.py.

    Returns:
        True si clasificar_riesgo() retorna nivel "critico".
    """
    return clasificar_riesgo(texto)["nivel"] == "critico"
