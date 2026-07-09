"""
LLMServicePort - Output Port (Arquitectura Hexagonal)

Define el contrato para servicios de generación de texto con LLMs.
La implementación concreta (Gemini) estará en adapters/outbound/.
"""
from abc import ABC, abstractmethod
from typing import List
from app.core.domain.models import Message


class LLMServicePort(ABC):
    """
    Puerto de salida para servicios LLM.
    
    Abstrae el proveedor específico (Gemini, OpenAI, Claude, etc.)
    """
    
    @abstractmethod
    async def generate_response(
        self,
        history: List[Message],
        system_instruction: str
    ) -> str:
        """
        Genera una respuesta basada en el historial de conversación.
        
        Args:
            history: Historial de mensajes
            system_instruction: Instrucciones del sistema para el modelo
            
        Returns:
            Texto de la respuesta generada
        """
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Verifica si el servicio LLM está disponible"""
        pass
