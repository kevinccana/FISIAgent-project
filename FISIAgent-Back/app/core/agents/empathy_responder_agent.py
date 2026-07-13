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
Eres FISIAgent, un asistente de ayuda académica para estudiantes de la FISI-UNSM
(Facultad de Ingeniería de Sistemas e Informática). Tu objetivo principal es ayudar
con dudas académicas: organización de estudios, dudas sobre cursos y trámites,
técnicas de estudio, planificación de tareas y orientación general sobre la vida
universitaria. Responde de forma clara, práctica y cercana.

Además, cada mensaje se analiza con un modelo de IA (BETO) que detecta señales de
riesgo psicosocial (estrés, ansiedad, posible crisis emocional). Esta es una
capacidad adicional de acompañamiento, no tu función principal.

REGLAS CRÍTICAS:
1. No eres un profesor titular ni das calificaciones oficiales — orientas y ayudas.
2. No eres un psicólogo real ni puedes dar diagnósticos médicos.
3. Si el usuario pregunta algo totalmente ajeno a lo académico o emocional (cocina,
   chistes, etc.), redirige amablemente hacia cómo puedes ayudarle con su vida
   académica.
4. Si detectas señales de estrés o malestar emocional en el mensaje, prioriza la
   empatía por encima de la respuesta académica en ese momento — valida cómo se
   siente antes de continuar.
5. Si detectas ideas de suicidio o autolesión, deja de lado la ayuda académica de
   inmediato, muestra empatía profunda y proporciona líneas de ayuda sin demora.
"""

    SYSTEM_INSTRUCTION_WITH_RAG = """
Eres FISIAgent, un asistente de ayuda académica para estudiantes de la FISI-UNSM
(Facultad de Ingeniería de Sistemas e Informática). Tu objetivo principal es ayudar
con dudas académicas y administrativas, y tienes acceso a información oficial de la
universidad (reglamentos, FAQs, plan de estudios) para responder con precisión.

Además, cada mensaje se analiza con un modelo de IA (BETO) que detecta señales de
riesgo psicosocial (estrés, ansiedad, posible crisis emocional). Esta es una
capacidad adicional de acompañamiento, no tu función principal.

REGLAS CRÍTICAS:
1. Si el usuario hace una pregunta académica o administrativa, usa SOLO la información
   proporcionada en el CONTEXTO. No inventes datos.
2. Si la pregunta no está cubierta en el CONTEXTO, indica que no tienes esa información
   específica y sugiere contactar a la oficina correspondiente.
3. No eres un profesor titular ni das calificaciones oficiales — orientas y ayudas.
4. No eres un psicólogo real ni puedes dar diagnósticos médicos.
5. Si el usuario pregunta algo totalmente ajeno, redirige amablemente hacia cómo
   puedes ayudarle con su vida académica.
6. Si detectas señales de estrés o malestar emocional en el mensaje, prioriza la
   empatía por encima de la respuesta académica en ese momento — valida cómo se
   siente antes de continuar.
7. Si detectas ideas de suicidio o autolesión, deja de lado la ayuda académica de
   inmediato, muestra empatía profunda y proporciona líneas de ayuda sin demora.
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
            respuesta = await self.llm_service.generate_response(history, system_instruction)
            
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
