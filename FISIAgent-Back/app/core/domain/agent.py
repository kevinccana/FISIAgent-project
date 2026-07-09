"""
Sistema de Agentes - Arquitectura Agentic AI (Innovators - InfoQ 2025)

Define la estructura base para agentes especializados que colaboran
en el procesamiento de conversaciones de apoyo emocional.

Patrón: Supervisor Multi-Agent
- CoordinadorAgente: Orquesta y decide qué agentes invocar
- Agentes especializados: Ejecutan tareas específicas
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import List, Optional, Any
from app.core.domain.models import Message


class AgentRole(Enum):
    """Roles de agentes en el sistema."""
    COORDINATOR = "coordinator"      # Orquestador principal
    RISK_ANALYZER = "risk_analyzer"  # Clasificación de riesgo
    RAG_RETRIEVER = "rag_retriever"  # Recuperación de información FISI
    RESOURCE_FINDER = "resource_finder"  # Búsqueda de recursos externos
    EMPATHY_RESPONDER = "empathy_responder"  # Generación de respuestas empáticas
    PLANNER = "planner"              # Planificación inteligente de tareas (Funcionalidad 3)


@dataclass
class AgentTask:
    """Tarea asignada a un agente."""
    agent_role: AgentRole
    input_data: Any
    priority: int = 1  # 1=alta, 2=media, 3=baja


@dataclass
class AgentResult:
    """Resultado de la ejecución de un agente."""
    agent_role: AgentRole
    success: bool
    data: Any
    error_message: Optional[str] = None


class Agent(ABC):
    """
    Clase base abstracta para todos los agentes.
    
    Cada agente es responsable de una tarea específica en el pipeline
    de procesamiento de conversaciones.
    """
    
    def __init__(self, role: AgentRole):
        self.role = role
    
    @abstractmethod
    async def execute(self, task: AgentTask) -> AgentResult:
        """
        Ejecuta la tarea asignada al agente.
        
        Args:
            task: Tarea con datos de entrada
            
        Returns:
            Resultado con datos procesados o error
        """
        pass
    
    @abstractmethod
    def can_handle(self, task: AgentTask) -> bool:
        """
        Verifica si el agente puede manejar la tarea.
        
        Returns:
            True si el agente es apropiado para esta tarea
        """
        pass
