"""
Modelos de dominio - Arquitectura Hexagonal

Entidades que representan conceptos del negocio, independientes de la infraestructura.
"""
from dataclasses import dataclass
from typing import Optional, Dict
from enum import Enum


class RiskLevel(str, Enum):
    """Niveles de riesgo psicosocial detectados"""
    CONTROL = "control"
    MODERADO = "moderado"
    CRITICO = "critico"


@dataclass
class Message:
    """Mensaje en una conversación"""
    role: str  # "user" o "model"
    text: str


@dataclass
class RiskAssessment:
    """Evaluación de riesgo de un mensaje"""
    level: RiskLevel
    probabilities: Dict[str, float]
    message_analyzed: str
    
    @property
    def is_critical(self) -> bool:
        return self.level == RiskLevel.CRITICO
    
    @property
    def needs_intervention(self) -> bool:
        return self.level in [RiskLevel.MODERADO, RiskLevel.CRITICO]


@dataclass
class VideoRecommendation:
    """Video de apoyo recomendado"""
    tipo: str
    titulo: str
    descripcion: str
    url: str
    duracion: str
    situacion: str


@dataclass
class ChatResponse:
    """Respuesta completa del sistema de chat"""
    respuesta: str
    nivel_riesgo: RiskLevel
    video_sugerido: Optional[VideoRecommendation]
    probabilidades: Dict[str, float]
