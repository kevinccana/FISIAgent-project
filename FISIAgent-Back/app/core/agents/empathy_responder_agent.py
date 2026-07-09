"""
EmpathyResponderAgent - Agente especializado en generar respuestas empáticas

Utiliza el LLMServicePort (Gemini) para generar respuestas comprensivas y cálidas,
opcionalmente incorporando contexto de RAG si está disponible.
"""
import logging
from typing import List
from app.core.domain.agent import Agent, AgentRole, AgentTask, AgentResult
from app.core.domain.models import Message, ChatResponse, RiskLevel
from app.ports.outbound.llm_service import LLMServicePort
from app.ports.outbound.video_recommender import VideoRecommenderPort

logger = logging.getLogger(__name__)


class EmpathyResponderAgent(Agent):
    """
    Agente que genera la respuesta empática final.
    
    Funcionalidades:
    - Genera respuesta usando LLM (Gemini)
    - Incorpora contexto de RAG si está disponible
    - Recomienda video si el riesgo es Moderado
    - Construye el ChatResponse completo
    """
    
    SYSTEM_INSTRUCTION_BASE = """
Eres un asistente de apoyo psicológico empático, cálido y profesional para estudiantes de FISI-UNSM.
Tu objetivo es escuchar activamente, validar emociones y ofrecer estrategias de afrontamiento básicas.

REGLAS CRÍTICAS:
1. No eres un psicólogo real ni puedes dar diagnósticos médicos.
2. Si el usuario pregunta temas irrelevantes (cocina, programación, chistes), 
   rechaza amablemente indicando que tu función es solo apoyo emocional.
3. Si detectas ideas de suicidio o autolesión, muestra empatía profunda 
   y proporciona líneas de ayuda inmediatamente.
"""
    
    SYSTEM_INSTRUCTION_WITH_RAG = """
Eres un asistente de apoyo psicológico empático, cálido y profesional para estudiantes de FISI-UNSM.
Tu objetivo es escuchar activamente, validar emociones y ofrecer estrategias de afrontamiento básicas.
Además, tienes acceso a información oficial de la universidad (reglamentos, FAQs, plan de estudios).

REGLAS CRÍTICAS:
1. Si el usuario hace una pregunta académica o administrativa, usa SOLO la información proporcionada 
   en el CONTEXTO. No inventes datos.
2. Si la pregunta no está cubierta en el CONTEXTO, indica que no tienes esa información específica 
   y sugiere contactar a la oficina correspondiente.
3. No eres un psicólogo real ni puedes dar diagnósticos médicos.
4. Si el usuario pregunta temas irrelevantes, rechaza amablemente.
5. Si detectas ideas de suicidio o autolesión, muestra empatía profunda 
   y proporciona líneas de ayuda inmediatamente.
"""
    
    def __init__(
        self,
        llm_service: LLMServicePort,
        video_recommender: VideoRecommenderPort
    ):
        super().__init__(AgentRole.EMPATHY_RESPONDER)
        self.llm_service = llm_service
        self.video_recommender = video_recommender
    
    async def execute(self, task: AgentTask) -> AgentResult:
        """
        Genera la respuesta empática final.
        
        Args:
            task.input_data: dict con:
                - history: List[Message]
                - rag_context: Optional[List[DocumentChunk]]
                - risk_assessment: RiskAssessment
        
        Returns:
            AgentResult con ChatResponse
        """
        try:
            data = task.input_data
            history = data.get("history", [])
            rag_context = data.get("rag_context", [])
            risk_assessment = data.get("risk_assessment")
            
            # Construir system instruction
            if rag_context:
                system_instruction = self._build_rag_instruction(rag_context)
            else:
                system_instruction = self.SYSTEM_INSTRUCTION_BASE
            
            # Generar respuesta con LLM
            logger.info(f"EmpathyResponderAgent: Generando respuesta con RAG={bool(rag_context)}")
            respuesta = self.llm_service.generate_response(history, system_instruction)
            
            # Recomendar video si es nivel Moderado
            video = None
            if risk_assessment and risk_assessment.level == RiskLevel.MODERADO:
                last_message = self._extract_last_user_message(history)
                video = self.video_recommender.recommend_video(
                    last_message,
                    RiskLevel.MODERADO
                )
            
            # Construir ChatResponse
            chat_response = ChatResponse(
                respuesta=respuesta,
                nivel_riesgo=risk_assessment.level if risk_assessment else RiskLevel.CONTROL,
                video_sugerido=video,
                probabilidades=risk_assessment.probabilities if risk_assessment else {}
            )
            
            return AgentResult(
                agent_role=self.role,
                success=True,
                data=chat_response
            )
            
        except Exception as e:
            logger.error(f"Error en EmpathyResponderAgent: {e}")
            # Respuesta de fallback
            fallback_response = ChatResponse(
                respuesta="Disculpa, estoy teniendo dificultades técnicas. ¿Podrías reformular tu pregunta?",
                nivel_riesgo=RiskLevel.CONTROL,
                video_sugerido=None,
                probabilidades={}
            )
            return AgentResult(
                agent_role=self.role,
                success=False,
                data=fallback_response,
                error_message=str(e)
            )
    
    def can_handle(self, task: AgentTask) -> bool:
        return task.agent_role == AgentRole.EMPATHY_RESPONDER
    
    def _extract_last_user_message(self, history: List[Message]) -> str:
        """Extrae el último mensaje del usuario."""
        for msg in reversed(history):
            if msg.role == "user":
                return msg.text
        return ""
    
    def _build_rag_instruction(self, rag_context: list) -> str:
        """
        Construye system instruction con contexto RAG.
        
        Formato:
        [Instrucción base]
        
        CONTEXTO (información oficial FISI-UNSM):
        ---
        [Chunk 1]
        ---
        [Chunk 2]
        ---
        """
        instruction = self.SYSTEM_INSTRUCTION_WITH_RAG + "\n\nCONTEXTO (información oficial FISI-UNSM):\n"
        
        for i, chunk in enumerate(rag_context, 1):
            instruction += f"\n--- Fragmento {i} (Fuente: {chunk.source}) ---\n"
            instruction += chunk.content + "\n"
        
        instruction += "\n---\n\nResponde basándote en este contexto cuando sea aplicable."
        return instruction
