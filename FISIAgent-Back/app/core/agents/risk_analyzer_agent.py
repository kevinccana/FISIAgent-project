"""
RiskAnalyzerAgent - Agente especializado en clasificación de riesgo psicosocial

Utiliza el RiskClassifierPort (BETO) para determinar el nivel de riesgo
del mensaje del usuario.
"""
import logging
from app.core.domain.agent import Agent, AgentRole, AgentTask, AgentResult
from app.ports.outbound.risk_classifier import RiskClassifierPort

logger = logging.getLogger(__name__)


class RiskAnalyzerAgent(Agent):
    """
    Agente que clasifica el riesgo emocional del mensaje.
    
    Delega la clasificación al RiskClassifierPort (arquitectura hexagonal).
    """
    
    def __init__(self, risk_classifier: RiskClassifierPort):
        super().__init__(AgentRole.RISK_ANALYZER)
        self.risk_classifier = risk_classifier
    
    async def execute(self, task: AgentTask) -> AgentResult:
        """
        Clasifica el riesgo del mensaje.
        
        Args:
            task.input_data: str (mensaje del usuario)
            
        Returns:
            AgentResult con RiskAssessment
        """
        try:
            message = task.input_data
            risk_assessment = self.risk_classifier.classify(message)
            
            logger.info(f"RiskAnalyzerAgent: Riesgo={risk_assessment.level.value}, "
                       f"Probs={risk_assessment.probabilities}")
            
            return AgentResult(
                agent_role=self.role,
                success=True,
                data=risk_assessment
            )
            
        except Exception as e:
            logger.error(f"Error en RiskAnalyzerAgent: {e}")
            return AgentResult(
                agent_role=self.role,
                success=False,
                data=None,
                error_message=str(e)
            )
    
    def can_handle(self, task: AgentTask) -> bool:
        return task.agent_role == AgentRole.RISK_ANALYZER
