"""
RiskClassifierPort - Output Port (Arquitectura Hexagonal)

Define el contrato para servicios de clasificación de riesgo psicosocial.
La implementación concreta (BETO) estará en adapters/outbound/.
"""
from abc import ABC, abstractmethod
from app.core.domain.models import RiskAssessment


class RiskClassifierPort(ABC):
    """
    Puerto de salida para clasificación de riesgo.
    
    Abstrae la tecnología específica (BETO, otro modelo, API externa, etc.)
    """
    
    @abstractmethod
    def classify(self, message: str) -> RiskAssessment:
        """
        Clasifica el nivel de riesgo psicosocial de un mensaje.
        
        Args:
            message: Texto del mensaje a analizar
            
        Returns:
            RiskAssessment con nivel de riesgo y probabilidades
        """
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Verifica si el clasificador está disponible"""
        pass
