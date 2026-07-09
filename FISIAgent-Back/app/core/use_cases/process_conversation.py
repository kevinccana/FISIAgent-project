"""
ProcessConversationUseCase - Caso de uso principal (Arquitectura Hexagonal)

Orquesta la lógica de negocio para procesar una conversación:
1. Clasifica el riesgo del último mensaje del usuario
2. Genera una respuesta empática con el LLM
3. Recomienda un video si es necesario

Esta clase NO conoce tecnologías específicas (BETO, Gemini, etc.)
Solo trabaja con las interfaces (ports).
"""
import logging
from typing import List
from app.core.domain.models import Message, ChatResponse, RiskLevel
from app.core.domain.exceptions import RiskClassificationError, LLMServiceError
from app.ports.inbound.chat_service import ChatServicePort
from app.ports.outbound.risk_classifier import RiskClassifierPort
from app.ports.outbound.llm_service import LLMServicePort
from app.ports.outbound.video_recommender import VideoRecommenderPort

logger = logging.getLogger(__name__)


class ProcessConversationUseCase(ChatServicePort):
    """
    Caso de uso: Procesar una conversación de chat.
    
    Implementa el port de entrada ChatServicePort, usando los ports de salida
    para interactuar con servicios externos.
    """
    
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
    
    def __init__(
        self,
        risk_classifier: RiskClassifierPort,
        llm_service: LLMServicePort,
        video_recommender: VideoRecommenderPort
    ):
        """
        Inyección de dependencias - Principio de Inversión de Dependencias (SOLID).
        
        El caso de uso depende de abstracciones (ports), no de implementaciones concretas.
        """
        self.risk_classifier = risk_classifier
        self.llm_service = llm_service
        self.video_recommender = video_recommender
    
    async def process_conversation(self, history: List[Message]) -> ChatResponse:
        """
        Procesa una conversación completa.
        
        Flujo:
        1. Extrae el último mensaje del usuario
        2. Clasifica el riesgo con el clasificador
        3. Genera respuesta con el LLM
        4. Recomienda video si es nivel moderado
        5. Retorna la respuesta completa
        """
        # 1. Extraer último mensaje del usuario
        ultimo_mensaje = self._extract_last_user_message(history)
        
        # 2. Clasificar riesgo
        try:
            risk_assessment = self.risk_classifier.classify(ultimo_mensaje)
            logger.info(f"Riesgo detectado: {risk_assessment.level} (p={risk_assessment.probabilities})")
        except Exception as e:
            logger.error(f"Error al clasificar riesgo: {e}")
            raise RiskClassificationError(f"No se pudo clasificar el riesgo: {str(e)}")
        
        # 3. Generar respuesta con LLM
        try:
            respuesta_texto = await self.llm_service.generate_response(
                history=history,
                system_instruction=self.SYSTEM_INSTRUCTION
            )
        except Exception as e:
            logger.error(f"Error al generar respuesta con LLM: {e}")
            # Fallback: respuesta genérica si el LLM falla
            respuesta_texto = self._get_fallback_response(risk_assessment.level)
        
        # 4. Recomendar video si es necesario
        video_sugerido = None
        if risk_assessment.level == RiskLevel.MODERADO:
            try:
                video_sugerido = self.video_recommender.recommend_video(
                    message=ultimo_mensaje,
                    risk_level=risk_assessment.level
                )
            except Exception as e:
                logger.warning(f"Error al recomendar video: {e}")
                # No crítico, continuamos sin video
        
        # 5. Construir respuesta completa
        return ChatResponse(
            respuesta=respuesta_texto,
            nivel_riesgo=risk_assessment.level,
            video_sugerido=video_sugerido,
            probabilidades=risk_assessment.probabilities
        )
    
    def _extract_last_user_message(self, history: List[Message]) -> str:
        """Extrae el último mensaje del usuario del historial"""
        for msg in reversed(history):
            if msg.role == "user":
                return msg.text
        return ""
    
    def _get_fallback_response(self, risk_level: RiskLevel) -> str:
        """Respuesta de emergencia si el LLM falla"""
        if risk_level == RiskLevel.CRITICO:
            return (
                "Veo que estás pasando por un momento muy difícil. "
                "Por favor, contacta con la Línea 113 (opción 5) para recibir apoyo inmediato. "
                "Están disponibles 24/7 y es gratuito."
            )
        elif risk_level == RiskLevel.MODERADO:
            return (
                "Entiendo que estás sintiendo presión. Es importante que cuides tu bienestar. "
                "Te recomiendo hablar con alguien de confianza o con el servicio de bienestar estudiantil."
            )
        else:
            return (
                "Estoy aquí para escucharte. ¿Hay algo específico en lo que pueda ayudarte hoy?"
            )
