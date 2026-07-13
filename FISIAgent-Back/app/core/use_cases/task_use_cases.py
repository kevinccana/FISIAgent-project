"""
Casos de uso para el Planificador Inteligente.

Funcionalidad 3: Lógica de negocio para gestión de tareas y planificación.
"""

import logging
from datetime import datetime, date, timedelta
from typing import List, Optional
from app.ports.outbound.task_repository import TaskRepositoryPort
from app.core.domain.task_models import (
    Task, TaskStatus, TaskPriority, TaskStatistics,
    TaskSuggestion, DailySchedule, Reminder
)
from app.core.agents.planner_agent import PlannerAgent
from app.core.domain.agent import AgentTask, AgentRole

logger = logging.getLogger(__name__)


class CreateTaskUseCase:
    """Caso de uso: Crear una nueva tarea."""
    
    def __init__(self, repository: TaskRepositoryPort, planner_agent: Optional[PlannerAgent] = None):
        """
        Args:
            repository: Repositorio de tareas
            planner_agent: Agente de IA (opcional) para sugerir prioridad
        """
        self.repository = repository
        self.planner_agent = planner_agent
    
    def execute(
        self,
        user_id: str,
        title: str,
        description: str,
        due_date: datetime,
        priority: Optional[TaskPriority] = None,
        category: str = "general",
        estimated_hours: float = 1.0,
        auto_suggest_priority: bool = False
    ) -> Task:
        """
        Crea una nueva tarea.
        
        Args:
            user_id: ID del usuario
            title: Título de la tarea
            description: Descripción
            due_date: Fecha límite
            priority: Prioridad (si es None y auto_suggest=True, usa IA)
            category: Categoría
            estimated_hours: Horas estimadas
            auto_suggest_priority: Si es True, usa IA para sugerir prioridad
        
        Returns:
            Tarea creada
        """
        # Si no hay prioridad y se pide sugerencia, usar IA
        if priority is None and auto_suggest_priority and self.planner_agent:
            priority = self._get_suggested_priority(user_id, title, description, due_date, category, estimated_hours)
        elif priority is None:
            priority = TaskPriority.MEDIUM  # Default
        
        # Crear entidad
        task = Task(
            user_id=user_id,
            title=title,
            description=description,
            due_date=due_date,
            priority=priority,
            category=category,
            estimated_hours=estimated_hours
        )
        
        # Persistir
        saved_task = self.repository.save_task(task)
        
        logger.info(f"Tarea creada: {saved_task.id} - {saved_task.title}")
        return saved_task
    
    def _get_suggested_priority(
        self,
        user_id: str,
        title: str,
        description: str,
        due_date: datetime,
        category: str,
        estimated_hours: float
    ) -> TaskPriority:
        """Usa el agente de IA para sugerir prioridad."""
        try:
            # Obtener tareas existentes para contexto
            existing_tasks = self.repository.get_user_tasks(user_id, limit=10)
            
            # Crear tarea temporal para análisis
            temp_task = Task(
                user_id=user_id,
                title=title,
                description=description,
                due_date=due_date,
                priority=TaskPriority.MEDIUM,  # Placeholder
                category=category,
                estimated_hours=estimated_hours
            )
            
            # Llamar al agente
            agent_task = AgentTask(
                agent_role=AgentRole.PLANNER,
                input_data={
                    "action": "suggest_priority",
                    "task": temp_task,
                    "existing_tasks": existing_tasks
                }
            )
            
            result = self.planner_agent.execute(agent_task)
            
            if result.success and isinstance(result.data, TaskSuggestion):
                logger.info(f"Prioridad sugerida por IA: {result.data.suggested_priority.label}")
                return result.data.suggested_priority
            else:
                logger.warning("Agente no pudo sugerir prioridad, usando MEDIUM")
                return TaskPriority.MEDIUM
        
        except Exception as e:
            logger.error(f"Error al sugerir prioridad: {e}")
            return TaskPriority.MEDIUM


class GetUpcomingTasksUseCase:
    """Caso de uso: Obtener tareas próximas a vencer."""
    
    def __init__(self, repository: TaskRepositoryPort):
        self.repository = repository
    
    def execute(self, user_id: str, days_ahead: int = 7, limit: Optional[int] = None) -> List[Task]:
        """
        Recupera tareas próximas ordenadas por urgencia.
        
        Args:
            user_id: ID del usuario
            days_ahead: Días hacia adelante
            limit: Límite de resultados
        
        Returns:
            Lista de tareas ordenadas por urgency_score
        """
        tasks = self.repository.get_upcoming_tasks(user_id, days_ahead, limit)
        logger.info(f"Recuperadas {len(tasks)} tareas próximas para user={user_id}")
        return tasks


class GetOverdueTasksUseCase:
    """Caso de uso: Obtener tareas vencidas."""
    
    def __init__(self, repository: TaskRepositoryPort):
        self.repository = repository
    
    def execute(self, user_id: str) -> List[Task]:
        """
        Recupera todas las tareas vencidas del usuario.
        
        Args:
            user_id: ID del usuario
        
        Returns:
            Lista de tareas vencidas
        """
        tasks = self.repository.get_overdue_tasks(user_id)
        logger.info(f"Usuario {user_id} tiene {len(tasks)} tareas vencidas")
        return tasks


class UpdateTaskUseCase:
    """Caso de uso: Actualizar una tarea."""
    
    def __init__(self, repository: TaskRepositoryPort):
        self.repository = repository
    
    def execute(
        self,
        task_id: int,
        title: Optional[str] = None,
        description: Optional[str] = None,
        due_date: Optional[datetime] = None,
        priority: Optional[TaskPriority] = None,
        status: Optional[TaskStatus] = None,
        category: Optional[str] = None,
        estimated_hours: Optional[float] = None
    ) -> Task:
        """
        Actualiza campos de una tarea existente.
        
        Args:
            task_id: ID de la tarea
            title: Nuevo título (opcional)
            description: Nueva descripción (opcional)
            due_date: Nueva fecha límite (opcional)
            priority: Nueva prioridad (opcional)
            status: Nuevo estado (opcional)
            category: Nueva categoría (opcional)
            estimated_hours: Nuevas horas estimadas (opcional)
        
        Returns:
            Tarea actualizada
        """
        # Recuperar tarea actual
        task = self.repository.get_task_by_id(task_id)
        if not task:
            raise ValueError(f"Tarea con ID {task_id} no encontrada")
        
        # Aplicar cambios
        if title is not None:
            task.title = title
        if description is not None:
            task.description = description
        if due_date is not None:
            task.due_date = due_date
        if priority is not None:
            task.priority = priority
        if status is not None:
            task.status = status
        if category is not None:
            task.category = category
        if estimated_hours is not None:
            task.estimated_hours = estimated_hours
        
        # Persistir
        updated_task = self.repository.update_task(task)
        logger.info(f"Tarea actualizada: {task_id}")
        return updated_task


class CompleteTaskUseCase:
    """Caso de uso: Marcar tarea como completada."""
    
    def __init__(self, repository: TaskRepositoryPort):
        self.repository = repository
    
    def execute(self, task_id: int) -> Task:
        """
        Marca una tarea como completada.
        
        Args:
            task_id: ID de la tarea
        
        Returns:
            Tarea actualizada
        """
        task = self.repository.get_task_by_id(task_id)
        if not task:
            raise ValueError(f"Tarea con ID {task_id} no encontrada")
        
        task.status = TaskStatus.COMPLETED
        task.completed_at = datetime.now()
        
        updated_task = self.repository.update_task(task)
        logger.info(f"Tarea completada: {task_id} - {task.title}")
        return updated_task


class DeleteTaskUseCase:
    """Caso de uso: Eliminar una tarea."""
    
    def __init__(self, repository: TaskRepositoryPort):
        self.repository = repository
    
    def execute(self, task_id: int) -> bool:
        """
        Elimina una tarea.
        
        Args:
            task_id: ID de la tarea
        
        Returns:
            True si se eliminó correctamente
        """
        success = self.repository.delete_task(task_id)
        if success:
            logger.info(f"Tarea eliminada: {task_id}")
        else:
            logger.warning(f"No se pudo eliminar tarea: {task_id}")
        return success


class GetTaskStatisticsUseCase:
    """Caso de uso: Obtener estadísticas de tareas."""
    
    def __init__(self, repository: TaskRepositoryPort):
        self.repository = repository
    
    def execute(self, user_id: str, days: int = 30) -> TaskStatistics:
        """
        Calcula estadísticas de tareas del usuario.
        
        Args:
            user_id: ID del usuario
            days: Número de días hacia atrás
        
        Returns:
            Estadísticas calculadas
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        stats = self.repository.get_statistics(user_id, start_date, end_date)
        logger.info(f"Estadísticas calculadas para user={user_id}: {stats.total_tasks} tareas")
        return stats


class AnalyzeDailyScheduleUseCase:
    """Caso de uso: Analizar carga de trabajo diaria con IA."""
    
    def __init__(self, repository: TaskRepositoryPort, planner_agent: PlannerAgent):
        self.repository = repository
        self.planner_agent = planner_agent
    
    async def execute(self, user_id: str, target_date: date) -> DailySchedule:
        """
        Analiza la carga de trabajo de un día específico.

        Args:
            user_id: ID del usuario
            target_date: Fecha a analizar

        Returns:
            Agenda diaria con recomendaciones
        """
        # Obtener tareas del día
        tasks = self.repository.get_tasks_for_date(user_id, target_date)

        # Llamar al agente para análisis
        agent_task = AgentTask(
            agent_role=AgentRole.PLANNER,
            input_data={
                "action": "analyze_schedule",
                "target_date": target_date,
                "tasks": tasks
            }
        )

        result = await self.planner_agent.execute(agent_task)
        
        if result.success and isinstance(result.data, DailySchedule):
            return result.data
        else:
            # Fallback sin IA
            total_hours = sum(t.estimated_hours for t in tasks)
            return DailySchedule(
                date=target_date,
                tasks=tasks,
                total_estimated_hours=total_hours,
                is_feasible=total_hours <= 8.0,
                recommendations=["Organiza tus tareas por prioridad."]
            )


class GetTaskOrganizationSuggestionsUseCase:
    """Caso de uso: Obtener sugerencias de organización general."""
    
    def __init__(self, repository: TaskRepositoryPort, planner_agent: PlannerAgent):
        self.repository = repository
        self.planner_agent = planner_agent
    
    async def execute(self, user_id: str) -> dict:
        """
        Analiza todas las tareas del usuario y da sugerencias.
        
        Args:
            user_id: ID del usuario
        
        Returns:
            Dict con diagnóstico y recomendaciones
        """
        # Obtener todas las tareas pendientes
        all_tasks = self.repository.get_user_tasks(user_id, limit=50)
        
        # Construir contexto
        pending = [t for t in all_tasks if t.status.value in [0, 1]]
        overdue = [t for t in all_tasks if t.is_overdue]
        
        context = f"Usuario con {len(all_tasks)} tareas, {len(pending)} pendientes, {len(overdue)} vencidas"
        
        # Llamar al agente
        agent_task = AgentTask(
            agent_role=AgentRole.PLANNER,
            input_data={
                "action": "suggest_organization",
                "tasks": all_tasks,
                "user_context": context
            }
        )
        
        result = await self.planner_agent.execute(agent_task)
        
        if result.success:
            return result.data
        else:
            return {
                "diagnosis": "Necesitas organizar mejor tus tareas.",
                "recommendations": [
                    "Prioriza las tareas vencidas.",
                    "Divide tareas grandes en pasos más pequeños.",
                    "Establece horarios específicos para trabajar en cada tarea."
                ],
                "resources": ["técnica Pomodoro", "método Eisenhower para priorizar"],
                "critical_tasks_count": len(overdue),
                "overdue_count": len(overdue)
            }


class CreateReminderUseCase:
    """Caso de uso: Crear recordatorio para una tarea."""
    
    def __init__(self, repository: TaskRepositoryPort):
        self.repository = repository
    
    def execute(self, task_id: int, remind_at: datetime, message: str = "") -> Reminder:
        """
        Crea un recordatorio para una tarea.
        
        Args:
            task_id: ID de la tarea
            remind_at: Fecha/hora del recordatorio
            message: Mensaje personalizado (opcional)
        
        Returns:
            Recordatorio creado
        """
        # Verificar que la tarea existe
        task = self.repository.get_task_by_id(task_id)
        if not task:
            raise ValueError(f"Tarea con ID {task_id} no encontrada")
        
        # Crear recordatorio
        reminder = Reminder(
            task_id=task_id,
            remind_at=remind_at,
            message=message or f"Recordatorio: {task.title}"
        )
        
        saved_reminder = self.repository.save_reminder(reminder)
        logger.info(f"Recordatorio creado: {saved_reminder.id} para tarea {task_id}")
        return saved_reminder
