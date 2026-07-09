"""
ChatService - Input Port (Arquitectura Hexagonal)

Define el contrato de lo que la aplicación puede hacer (casos de uso).
"""
from abc import ABC, abstractmethod
from typing import List
from app.core.domain.models import Message, ChatResponse


class ChatServicePort(ABC):
    """
    Puerto de entrada para el servicio de chat.
    
    Define las operaciones que los adaptadores de entrada (ej: API REST)
    pueden invocar en la aplicación.
    """
    
    @abstractmethod
    async def process_conversation(self, history: List[Message]) -> ChatResponse:
        """
        Procesa una conversación completa y retorna una respuesta.
        
        Args:
            history: Historial de mensajes de la conversación
            
        Returns:
            ChatResponse con la respuesta, nivel de riesgo y recursos sugeridos
        """
        pass
