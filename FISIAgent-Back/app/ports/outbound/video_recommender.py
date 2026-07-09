"""
VideoRecommenderPort - Output Port (Arquitectura Hexagonal)

Define el contrato para servicios de recomendación de videos de apoyo.
"""
from abc import ABC, abstractmethod
from typing import Optional
from app.core.domain.models import VideoRecommendation, RiskLevel


class VideoRecommenderPort(ABC):
    """
    Puerto de salida para recomendación de videos.
    
    Puede tener múltiples implementaciones: selección con IA, reglas, etc.
    """
    
    @abstractmethod
    def recommend_video(
        self,
        message: str,
        risk_level: RiskLevel
    ) -> Optional[VideoRecommendation]:
        """
        Recomienda un video de apoyo según el mensaje y nivel de riesgo.
        
        Args:
            message: Mensaje del usuario
            risk_level: Nivel de riesgo detectado
            
        Returns:
            VideoRecommendation si aplica, None si no hay video para ese nivel
        """
        pass
