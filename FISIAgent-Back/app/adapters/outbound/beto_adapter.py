"""
BETOAdapter - Outbound Adapter (Arquitectura Hexagonal)

Implementa el port RiskClassifierPort usando el modelo BETO.
Encapsula la lógica de clasificación de riesgo psicosocial.
"""
import logging
import os
from pathlib import Path
from typing import Dict, Optional
from app.core.domain.models import RiskAssessment, RiskLevel
from app.ports.outbound.risk_classifier import RiskClassifierPort

logger = logging.getLogger(__name__)

# ── Constantes ─────────────────────────────────────────────────────────────────
# parents[4]: beto_adapter.py -> outbound -> adapters -> app -> FISIAgent-Back -> repo root
_REPO_ROOT = Path(__file__).resolve().parents[4]
_MODEL_DIR = Path(os.getenv("BETO_MODEL_PATH", _REPO_ROOT / "BETO_model"))

UMBRAL_CRITICO  = 0.30
UMBRAL_MODERADO = 0.45

# Palabras clave de crisis (modo fallback)
_PALABRAS_CRISIS = [
    "suicidio", "suicidarme", "quitarme la vida",
    "morir", "morirme", "matarme", "no quiero vivir",
    "acabar con todo", "no tiene sentido vivir", "hacerme daño",
]


class BETOAdapter(RiskClassifierPort):
    """
    Adapter que implementa clasificación de riesgo usando el modelo BETO.
    
    Singleton pattern: el modelo se carga una sola vez en memoria.
    """
    
    def __init__(self):
        self._tokenizer: Optional[any] = None
        self._model: Optional[any] = None
        self._modelo_disponible = False
    
    def load_model(self) -> bool:
        """
        Carga el modelo BETO en memoria.
        
        Debe llamarse al iniciar la aplicación (startup event).
        
        Returns:
            True si el modelo se cargó correctamente
        """
        try:
            from transformers import AutoTokenizer, AutoModelForSequenceClassification

            if not _MODEL_DIR.exists():
                logger.warning(
                    f"[BETO] Carpeta del modelo no encontrada: {_MODEL_DIR}. "
                    "Usando modo fallback (palabras clave)."
                )
                return False

            logger.info(f"[BETO] Cargando modelo desde: {_MODEL_DIR}")
            self._tokenizer = AutoTokenizer.from_pretrained(str(_MODEL_DIR))
            self._model = AutoModelForSequenceClassification.from_pretrained(str(_MODEL_DIR))
            self._model.eval()  # Modo inferencia

            self._modelo_disponible = True
            logger.info("[BETO] Modelo cargado correctamente.")
            return True

        except Exception as exc:
            logger.error(f"[BETO] Error al cargar el modelo: {exc}")
            self._modelo_disponible = False
            return False
    
    def classify(self, message: str) -> RiskAssessment:
        """
        Clasifica el nivel de riesgo psicosocial de un mensaje.
        
        Implementación del port RiskClassifierPort.
        """
        if not self._modelo_disponible:
            return self._fallback_classification(message)
        
        try:
            import torch

            inputs = self._tokenizer(
                message,
                return_tensors="pt",
                truncation=True,
                max_length=128,
                padding=True,
            )

            with torch.no_grad():
                logits = self._model(**inputs).logits
                probs = torch.softmax(logits, dim=-1)[0].tolist()

            p_control, p_moderado, p_critico = probs

            probabilidades = {
                "control": round(p_control, 4),
                "moderado": round(p_moderado, 4),
                "critico": round(p_critico, 4),
            }

            # Determinar nivel según umbrales (Crítico tiene prioridad)
            if p_critico >= UMBRAL_CRITICO:
                nivel = RiskLevel.CRITICO
            elif p_moderado >= UMBRAL_MODERADO:
                nivel = RiskLevel.MODERADO
            else:
                nivel = RiskLevel.CONTROL

            return RiskAssessment(
                level=nivel,
                probabilities=probabilidades,
                message_analyzed=message
            )

        except Exception as exc:
            logger.error(f"[BETO] Error durante inferencia: {exc}")
            return self._fallback_classification(message)
    
    def is_available(self) -> bool:
        """Verifica si el modelo está disponible"""
        return self._modelo_disponible
    
    def _fallback_classification(self, message: str) -> RiskAssessment:
        """
        Clasificación de emergencia por palabras clave.
        
        Solo detecta nivel Crítico para evitar falsos positivos.
        """
        texto_lower = message.lower()
        
        if any(palabra in texto_lower for palabra in _PALABRAS_CRISIS):
            nivel = RiskLevel.CRITICO
        else:
            nivel = RiskLevel.CONTROL
        
        return RiskAssessment(
            level=nivel,
            probabilities={
                "control": 0.0,
                "moderado": 0.0,
                "critico": 1.0 if nivel == RiskLevel.CRITICO else 0.0
            },
            message_analyzed=message
        )
