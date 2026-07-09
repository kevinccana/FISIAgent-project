"""
Router API para el Planificador Inteligente.

Funcionalidad 3: Endpoints REST para gestión de tareas y planificación.
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime, date
from app.core.domain.task_models import TaskPriority, TaskStatus
from app.core.use_cases.task_use_cases import (
    CreateTaskUseCase,
    GetUpcomingTasksUseCase,
    GetOverdueTasksUseCase,
    UpdateTaskUseCase,
    CompleteTaskUseCase,
    DeleteTaskUseCase,
    GetTaskStatisticsUseCase,
    AnalyzeDailyScheduleUseCase,
    GetTaskOrganizationSuggestionsUseCase,
    CreateReminderUseCase
)

# DTOs (Data Transfer Objects)

class CreateTaskDTO(BaseModel):
    """DTO para crear una tarea."""
    user_id: str = Field(..., description="ID del usuario")
    title: str = Field(..., max_length=200, description="Título de la tarea")
    description: str = Field(default="", max_length=1000, description="Descripción detallada")
    due_date: datetime = Field(..., description="Fecha y hora límite")
    priority: Optional[int] = Field(None, ge=0, le=3, description="Prioridad (0-3), None para sugerir con IA")
    category: str = Field(default="general", description="Categoría (académico, personal, bienestar, etc.)")
    estimated_hours: float = Field(default=1.0, gt=0, le=100, description="Horas estimadas")
    auto_suggest_priority: bool = Field(default=False, description="Usar IA para sugerir prioridad")


class UpdateTaskDTO(BaseModel):
    """DTO para actualizar una tarea."""
    title: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    due_date: Optional[datetime] = None
    priority: Optional[int] = Field(None, ge=0, le=3)
    status: Optional[int] = Field(None, ge=0, le=3)
    category: Optional[str] = None
    estimated_hours: Optional[float] = Field(None, gt=0, le=100)


class TaskDTO(BaseModel):
    """DTO de respuesta para una tarea."""
    id: int
    user_id: str
    title: str
    description: str
    due_date: datetime
    priority: int
    priority_label: str
    priority_emoji: str
    status: int
    status_label: str
    status_emoji: str
    category: str
    estimated_hours: float
    is_overdue: bool
    days_until_due: int
    urgency_score: float
    completed_at: Optional[datetime]
    created_at: Optional[datetime]


class TaskStatisticsDTO(BaseModel):
    """DTO de respuesta para estadísticas."""
    user_id: str
    period_start: datetime
    period_end: datetime
    total_tasks: int
    completed_tasks: int
    pending_tasks: int
    overdue_tasks: int
    completion_rate: float
    completion_percentage: float
    avg_completion_time_hours: float
    tasks_by_priority: dict
    tasks_by_category: dict
    productivity_trend: str


class DailyScheduleDTO(BaseModel):
    """DTO de respuesta para agenda diaria."""
    date: date
    tasks: List[TaskDTO]
    total_estimated_hours: float
    is_feasible: bool
    is_overloaded: bool
    recommendations: List[str]


class OrganizationSuggestionsDTO(BaseModel):
    """DTO de respuesta para sugerencias de organización."""
    diagnosis: str
    recommendations: List[str]
    critical_tasks_count: int
    overdue_count: int


class CreateReminderDTO(BaseModel):
    """DTO para crear un recordatorio."""
    task_id: int
    remind_at: datetime
    message: Optional[str] = ""


class ReminderDTO(BaseModel):
    """DTO de respuesta para un recordatorio."""
    id: int
    task_id: int
    remind_at: datetime
    message: str
    is_sent: bool
    created_at: Optional[datetime]


# Router

router = APIRouter(prefix="/tasks", tags=["Planificador Inteligente"])

# Variables globales (inyectadas por main.py)
create_task_uc: Optional[CreateTaskUseCase] = None
get_upcoming_uc: Optional[GetUpcomingTasksUseCase] = None
get_overdue_uc: Optional[GetOverdueTasksUseCase] = None
update_task_uc: Optional[UpdateTaskUseCase] = None
complete_task_uc: Optional[CompleteTaskUseCase] = None
delete_task_uc: Optional[DeleteTaskUseCase] = None
get_statistics_uc: Optional[GetTaskStatisticsUseCase] = None
analyze_schedule_uc: Optional[AnalyzeDailyScheduleUseCase] = None
get_suggestions_uc: Optional[GetTaskOrganizationSuggestionsUseCase] = None
create_reminder_uc: Optional[CreateReminderUseCase] = None


def configure_task_router(
    create_task: CreateTaskUseCase,
    get_upcoming: GetUpcomingTasksUseCase,
    get_overdue: GetOverdueTasksUseCase,
    update_task: UpdateTaskUseCase,
    complete_task: CompleteTaskUseCase,
    delete_task: DeleteTaskUseCase,
    get_statistics: GetTaskStatisticsUseCase,
    analyze_schedule: AnalyzeDailyScheduleUseCase,
    get_suggestions: GetTaskOrganizationSuggestionsUseCase,
    create_reminder: CreateReminderUseCase
):
    """
    Configura el router con las dependencias (inyección).
    
    Debe ser llamado desde main.py durante el bootstrap.
    """
    global create_task_uc, get_upcoming_uc, get_overdue_uc, update_task_uc, complete_task_uc
    global delete_task_uc, get_statistics_uc, analyze_schedule_uc, get_suggestions_uc, create_reminder_uc
    
    create_task_uc = create_task
    get_upcoming_uc = get_upcoming
    get_overdue_uc = get_overdue
    update_task_uc = update_task
    complete_task_uc = complete_task
    delete_task_uc = delete_task
    get_statistics_uc = get_statistics
    analyze_schedule_uc = analyze_schedule
    get_suggestions_uc = get_suggestions
    create_reminder_uc = create_reminder


# Endpoints

@router.post("/", response_model=TaskDTO, status_code=201)
def create_task(data: CreateTaskDTO):
    """
    Crea una nueva tarea.
    
    Si `auto_suggest_priority=True` y `priority=None`, usa IA para sugerir la prioridad.
    """
    try:
        priority_enum = TaskPriority(data.priority) if data.priority is not None else None
        
        task = create_task_uc.execute(
            user_id=data.user_id,
            title=data.title,
            description=data.description,
            due_date=data.due_date,
            priority=priority_enum,
            category=data.category,
            estimated_hours=data.estimated_hours,
            auto_suggest_priority=data.auto_suggest_priority
        )
        
        return _task_to_dto(task)
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al crear tarea: {str(e)}")


@router.get("/upcoming/{user_id}", response_model=List[TaskDTO])
def get_upcoming_tasks(
    user_id: str,
    days: int = Query(default=7, ge=1, le=90, description="Días hacia adelante"),
    limit: Optional[int] = Query(default=None, ge=1, le=100, description="Límite de resultados")
):
    """
    Obtiene tareas próximas a vencer, ordenadas por urgencia.
    """
    try:
        tasks = get_upcoming_uc.execute(user_id, days, limit)
        return [_task_to_dto(task) for task in tasks]
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener tareas: {str(e)}")


@router.get("/overdue/{user_id}", response_model=List[TaskDTO])
def get_overdue_tasks(user_id: str):
    """
    Obtiene todas las tareas vencidas del usuario.
    """
    try:
        tasks = get_overdue_uc.execute(user_id)
        return [_task_to_dto(task) for task in tasks]
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener tareas vencidas: {str(e)}")


@router.get("/statistics/{user_id}", response_model=TaskStatisticsDTO)
def get_statistics(
    user_id: str,
    days: int = Query(default=30, ge=1, le=365, description="Días hacia atrás")
):
    """
    Obtiene estadísticas de tareas del usuario.
    """
    try:
        stats = get_statistics_uc.execute(user_id, days)
        
        return TaskStatisticsDTO(
            user_id=stats.user_id,
            period_start=stats.period_start,
            period_end=stats.period_end,
            total_tasks=stats.total_tasks,
            completed_tasks=stats.completed_tasks,
            pending_tasks=stats.pending_tasks,
            overdue_tasks=stats.overdue_tasks,
            completion_rate=stats.completion_rate,
            completion_percentage=stats.completion_percentage,
            avg_completion_time_hours=stats.avg_completion_time_hours,
            tasks_by_priority=stats.tasks_by_priority,
            tasks_by_category=stats.tasks_by_category,
            productivity_trend=stats.productivity_trend
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al calcular estadísticas: {str(e)}")


@router.get("/schedule/{user_id}/{target_date}", response_model=DailyScheduleDTO)
def analyze_daily_schedule(user_id: str, target_date: date):
    """
    Analiza la carga de trabajo de un día específico con IA.
    
    Devuelve las tareas del día y recomendaciones inteligentes.
    """
    try:
        schedule = analyze_schedule_uc.execute(user_id, target_date)
        
        return DailyScheduleDTO(
            date=schedule.date,
            tasks=[_task_to_dto(task) for task in schedule.tasks],
            total_estimated_hours=schedule.total_estimated_hours,
            is_feasible=schedule.is_feasible,
            is_overloaded=schedule.is_overloaded,
            recommendations=schedule.recommendations
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al analizar agenda: {str(e)}")


@router.get("/suggestions/{user_id}", response_model=OrganizationSuggestionsDTO)
def get_organization_suggestions(user_id: str):
    """
    Obtiene sugerencias de organización general usando IA.
    
    Analiza todas las tareas del usuario y proporciona diagnóstico y recomendaciones.
    """
    try:
        suggestions = get_suggestions_uc.execute(user_id)
        
        return OrganizationSuggestionsDTO(
            diagnosis=suggestions["diagnosis"],
            recommendations=suggestions["recommendations"],
            critical_tasks_count=suggestions["critical_tasks_count"],
            overdue_count=suggestions["overdue_count"]
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al generar sugerencias: {str(e)}")


@router.put("/{task_id}", response_model=TaskDTO)
def update_task(task_id: int, data: UpdateTaskDTO):
    """
    Actualiza una tarea existente.
    """
    try:
        priority_enum = TaskPriority(data.priority) if data.priority is not None else None
        status_enum = TaskStatus(data.status) if data.status is not None else None
        
        task = update_task_uc.execute(
            task_id=task_id,
            title=data.title,
            description=data.description,
            due_date=data.due_date,
            priority=priority_enum,
            status=status_enum,
            category=data.category,
            estimated_hours=data.estimated_hours
        )
        
        return _task_to_dto(task)
    
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al actualizar tarea: {str(e)}")


@router.post("/{task_id}/complete", response_model=TaskDTO)
def complete_task(task_id: int):
    """
    Marca una tarea como completada.
    """
    try:
        task = complete_task_uc.execute(task_id)
        return _task_to_dto(task)
    
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al completar tarea: {str(e)}")


@router.delete("/{task_id}")
def delete_task(task_id: int):
    """
    Elimina una tarea.
    """
    try:
        success = delete_task_uc.execute(task_id)
        
        if success:
            return {"message": "Tarea eliminada correctamente", "id": task_id}
        else:
            raise HTTPException(status_code=404, detail="Tarea no encontrada")
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al eliminar tarea: {str(e)}")


@router.post("/reminders", response_model=ReminderDTO, status_code=201)
def create_reminder(data: CreateReminderDTO):
    """
    Crea un recordatorio para una tarea.
    """
    try:
        reminder = create_reminder_uc.execute(
            task_id=data.task_id,
            remind_at=data.remind_at,
            message=data.message
        )
        
        return ReminderDTO(
            id=reminder.id,
            task_id=reminder.task_id,
            remind_at=reminder.remind_at,
            message=reminder.message,
            is_sent=reminder.is_sent,
            created_at=reminder.created_at
        )
    
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al crear recordatorio: {str(e)}")


# Helpers

def _task_to_dto(task) -> TaskDTO:
    """Convierte una entidad Task a DTO."""
    return TaskDTO(
        id=task.id,
        user_id=task.user_id,
        title=task.title,
        description=task.description,
        due_date=task.due_date,
        priority=task.priority.value,
        priority_label=task.priority.label,
        priority_emoji=task.priority.emoji,
        status=task.status.value,
        status_label=task.status.label,
        status_emoji=task.status.emoji,
        category=task.category,
        estimated_hours=task.estimated_hours,
        is_overdue=task.is_overdue,
        days_until_due=task.days_until_due,
        urgency_score=task.urgency_score,
        completed_at=task.completed_at,
        created_at=task.created_at
    )
