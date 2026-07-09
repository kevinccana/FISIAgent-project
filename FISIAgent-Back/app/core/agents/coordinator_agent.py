"""
CoordinadorAgente - Agente supervisor (Agentic AI)

Responsabilidades:
1. Analizar la consulta del usuario
2. Decidir qué agentes especializados invocar
3. Coordinar la ejecución en el orden apropiado
4. Agregar resultados y retornar respuesta final
"""
import logging
from typing import List, Dict
from app.core.domain.agent import Agent, AgentRole, AgentTask, AgentResult
from app.core.domain.models import Message, ChatResponse

logger = logging.getLogger(__name__)


class CoordinadorAgente(Agent):
    """
    Agente coordinador - implementa patrón Supervisor.
    
    Decide qué agentes especializados ejecutar según el contexto:
    - Si es pregunta académica → RAGRetrieverAgent
    - Si hay riesgo emocional → RiskAnalyzerAgent
    - Si solicita recursos → ResourceFinderAgent
    - Siempre → EmpathyResponderAgent (respuesta final)
    """
    
    def __init__(self, agents: Dict[AgentRole, Agent]):
        """
        Inicializa el coordinador con los agentes disponibles.
        
        Args:
            agents: Diccionario {AgentRole: Agent} con agentes especializados
        """
        super().__init__(AgentRole.COORDINATOR)
        self.agents = agents
        logger.info(f"CoordinadorAgente inicializado con {len(agents)} agentes")
    
    async def execute(self, task: AgentTask) -> AgentResult:
        """
        Coordina la ejecución de múltiples agentes.
        
        Flujo:
        1. Analiza el mensaje del usuario
        2. Decide qué agentes invocar
        3. Ejecuta agentes en orden (risk → RAG → empathy)
        4. Agrega resultados en ChatResponse
        """
        try:
            history: List[Message] = task.input_data
            last_message = self._extract_last_user_message(history)
            
            # Plan de ejecución
            execution_plan = self._create_execution_plan(last_message)
            logger.info(f"Plan de ejecución: {[t.agent_role.value for t in execution_plan]}")
            
            # ═══════════════════════════════════════════════════════════════════
            # Ejecutar agentes secuencialmente y acumular resultados
            # ═══════════════════════════════════════════════════════════════════
            
            risk_assessment = None
            rag_context = []
            
            for agent_task in execution_plan:
                agent = self.agents.get(agent_task.agent_role)
                if not agent:
                    logger.warning(f"Agente {agent_task.agent_role.value} no disponible")
                    continue
                
                # Ejecutar según el tipo de agente
                if agent_task.agent_role == AgentRole.RISK_ANALYZER:
                    result = await agent.execute(agent_task)
                    if result.success:
                        risk_assessment = result.data
                        logger.info(f"✓ Riesgo: {risk_assessment.level.value}")
                    else:
                        logger.warning(f"⚠ RiskAnalyzerAgent falló: {result.error_message}")
                
                elif agent_task.agent_role == AgentRole.RAG_RETRIEVER:
                    result = await agent.execute(agent_task)
                    if result.success and result.data:
                        rag_context = result.data
                        logger.info(f"✓ RAG: {len(rag_context)} chunks recuperados")
                    else:
                        logger.info(f"ℹ RAG sin resultados o no disponible")
                
                elif agent_task.agent_role == AgentRole.EMPATHY_RESPONDER:
                    # Pasar todos los datos acumulados al agente de respuesta
                    empathy_task = AgentTask(
                        agent_role=AgentRole.EMPATHY_RESPONDER,
                        input_data={
                            "history": history,
                            "rag_context": rag_context,
                            "risk_assessment": risk_assessment
                        },
                        priority=1
                    )
                    result = await agent.execute(empathy_task)
                    if result.success:
                        chat_response = result.data
                        logger.info("✓ Respuesta empática generada")
                        
                        return AgentResult(
                            agent_role=self.role,
                            success=True,
                            data=chat_response
                        )
                    else:
                        logger.error(f"⚠ EmpathyResponderAgent falló: {result.error_message}")
                        # Retornar el fallback que el agente ya generó
                        return AgentResult(
                            agent_role=self.role,
                            success=False,
                            data=result.data,  # Fallback response
                            error_message=result.error_message
                        )
            
            # Si llegamos aquí, algo salió mal
            logger.error("CoordinadorAgente: No se pudo generar respuesta")
            return AgentResult(
                agent_role=self.role,
                success=False,
                data=None,
                error_message="No se completó el pipeline de agentes"
            )
            
        except Exception as e:
            logger.error(f"Error en CoordinadorAgente: {e}", exc_info=True)
            return AgentResult(
                agent_role=self.role,
                success=False,
                data=None,
                error_message=str(e)
            )
    
    def can_handle(self, task: AgentTask) -> bool:
        """El coordinador siempre puede manejar tareas de coordinación."""
        return task.agent_role == AgentRole.COORDINATOR
    
    def _extract_last_user_message(self, history: List[Message]) -> str:
        """Extrae el último mensaje del usuario."""
        for msg in reversed(history):
            if msg.role == "user":
                return msg.text
        return ""
    
    def _create_execution_plan(self, message: str) -> List[AgentTask]:
        """
        Crea el plan de ejecución basado en el mensaje.
        
        Heurísticas:
        - Si contiene palabras clave académicas → RAG
        - Siempre → Risk + Empathy
        """
        plan = []
        
        # 1. Clasificación de riesgo (siempre)
        plan.append(AgentTask(
            agent_role=AgentRole.RISK_ANALYZER,
            input_data=message,
            priority=1
        ))
        
        # 2. RAG si parece pregunta académica
        academic_keywords = [
            "crédito", "curso", "ciclo", "matrícula", "nota", "desaprobar",
            "retiro", "convalidar", "beca", "bienestar", "psicólogo",
            "reglamento", "plan", "horario", "laboratorio", "biblioteca"
        ]
        if any(keyword in message.lower() for keyword in academic_keywords):
            plan.append(AgentTask(
                agent_role=AgentRole.RAG_RETRIEVER,
                input_data=message,
                priority=1
            ))
        
        # 3. Generación de respuesta empática (siempre, al final)
        plan.append(AgentTask(
            agent_role=AgentRole.EMPATHY_RESPONDER,
            input_data={"message": message, "rag_available": len(plan) > 1},
            priority=1
        ))
        
        return plan
    
    def _aggregate_results(self, results: Dict[AgentRole, AgentResult]) -> ChatResponse:
        """
        Agrega resultados de todos los agentes en un ChatResponse.
        
        Prioridad:
        - Risk: nivel de riesgo + probabilidades
        - RAG: contexto agregado a la respuesta
        - Empathy: respuesta final del LLM
        """
        # Extraer datos de los agentes
        risk_result = results.get(AgentRole.RISK_ANALYZER)
        rag_result = results.get(AgentRole.RAG_RETRIEVER)
        empathy_result = results.get(AgentRole.EMPATHY_RESPONDER)
        
        # Construir ChatResponse
        # (La estructura final se define en el use case que usa este coordinador)
        return empathy_result.data if empathy_result else None
