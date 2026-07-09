"""
RAGRetrieverAgent - Agente especializado en recuperación de información

Utiliza el RAGServicePort para buscar información contextual de documentos
FISI-UNSM cuando el usuario hace preguntas académicas o administrativas.
"""
import logging
from app.core.domain.agent import Agent, AgentRole, AgentTask, AgentResult
from app.ports.outbound.rag_service import RAGServicePort

logger = logging.getLogger(__name__)


class RAGRetrieverAgent(Agent):
    """
    Agente que recupera información contextual de documentos FISI.
    
    Casos de uso:
    - "¿Cuántos créditos mínimos debo llevar?" → busca en plan_estudios.txt
    - "¿Hay psicólogo en la universidad?" → busca en reglamento_bienestar.txt
    - "¿Puedo retirarme de un curso?" → busca en faq_estudiantes.txt
    """
    
    def __init__(self, rag_service: RAGServicePort):
        super().__init__(AgentRole.RAG_RETRIEVER)
        self.rag_service = rag_service
    
    async def execute(self, task: AgentTask) -> AgentResult:
        """
        Recupera información relevante de documentos.
        
        Args:
            task.input_data: str (consulta del usuario)
            
        Returns:
            AgentResult con List[DocumentChunk] o lista vacía
        """
        try:
            query = task.input_data
            
            if not self.rag_service.is_available():
                logger.warning("RAGRetrieverAgent: Servicio RAG no disponible")
                return AgentResult(
                    agent_role=self.role,
                    success=False,
                    data=[],
                    error_message="RAG no disponible"
                )
            
            # Recuperar chunks relevantes (top 3)
            chunks = self.rag_service.retrieve_context(query, top_k=3)
            
            logger.info(f"RAGRetrieverAgent: Recuperados {len(chunks)} chunks para '{query[:40]}...'")
            
            return AgentResult(
                agent_role=self.role,
                success=True,
                data=chunks
            )
            
        except Exception as e:
            logger.error(f"Error en RAGRetrieverAgent: {e}")
            return AgentResult(
                agent_role=self.role,
                success=False,
                data=[],
                error_message=str(e)
            )
    
    def can_handle(self, task: AgentTask) -> bool:
        return task.agent_role == AgentRole.RAG_RETRIEVER
