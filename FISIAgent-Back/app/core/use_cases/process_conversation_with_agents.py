"""
ProcessConversationWithAgentsUseCase - Caso de uso con Agentic AI

Version mejorada que utiliza el sistema multi-agente para procesar conversaciones.
Reemplaza la lógica secuencial con un coordinador que orquesta agentes especializados.

Innovación (InfoQ 2025 - Innovators):
- Agentic AI: Múltiples agentes autónomos colaborando
- RAG integrado: Contexto de documentos FISI-UNSM
"""
import logging
from typing import List
from app.core.domain.models import Message, ChatResponse
from app.core.domain.agent import AgentRole, AgentTask
from app.ports.inbound.chat_service import ChatServicePort
from app.core.agents import CoordinadorAgente

logger = logging.getLogger(__name__)


class ProcessConversationWithAgentsUseCase(ChatServicePort):
    """
    Caso de uso que delega el procesamiento a un sistema multi-agente.
    
    Arquitectura:
    - CoordinadorAgente decide qué agentes invocar
    - RiskAnalyzerAgent clasifica riesgo
    - RAGRetrieverAgent busca información contextual
    - EmpathyResponderAgent genera respuesta empática
    
    Ventajas sobre el flujo secuencial:
    - Escalabilidad: fácil agregar nuevos agentes
    - Flexibilidad: el coordinador adapta el pipeline según el contexto
    - Observabilidad: cada agente puede ser monitoreado independientemente
    """
    
    def __init__(self, coordinator: CoordinadorAgente):
        """
        Inyección de dependencias con el coordinador.
        
        Args:
            coordinator: CoordinadorAgente que orquesta agentes especializados
        """
        self.coordinator = coordinator
        logger.info("ProcessConversationWithAgentsUseCase inicializado")
    
    async def process_conversation(self, history: List[Message]) -> ChatResponse:
        """
        Procesa la conversación usando el sistema multi-agente.
        
        Flujo:
        1. Crea tarea de coordinación con el historial
        2. El coordinador decide qué agentes invocar
        3. Los agentes ejecutan en el orden apropiado
        4. Retorna el ChatResponse agregado
        """
        try:
            # Crear tarea para el coordinador
            task = AgentTask(
                agent_role=AgentRole.COORDINATOR,
                input_data=history,
                priority=1
            )
            
            # Ejecutar coordinador (orquesta todos los agentes)
            result = await self.coordinator.execute(task)
            
            if not result.success:
                logger.error(f"Coordinador falló: {result.error_message}")
                # Retornar respuesta de fallback
                return ChatResponse(
                    respuesta="Disculpa, estoy teniendo problemas técnicos. ¿Podrías intentar de nuevo?",
                    nivel_riesgo=None,
                    video_sugerido=None,
                    probabilidades={}
                )
            
            return result.data
            
        except Exception as e:
            logger.error(f"Error en ProcessConversationWithAgentsUseCase: {e}")
            # Respuesta de emergencia
            return ChatResponse(
                respuesta="Lamento las molestias. El sistema está experimentando dificultades.",
                nivel_riesgo=None,
                video_sugerido=None,
                probabilidades={}
            )
