"""
Modelos de dominio para el Planificador Inteligente.

Funcionalidad 3: Sistema de gestión de tareas y recordatorios
con priorización inteligente mediante IA.
"""

from dataclasses import dataclass, field
from datetime import datetime, date, timedelta
from enum import IntEnum
from typing import Optional, List


class TaskPriority(IntEnum):
    """Niveles de prioridad de tareas (0=más alta, 3=más baja)."""
    URGENT = 0      # Urgente e importante
    HIGH = 1        # Alta prioridad
    MEDIUM = 2      # Prioridad media
    LOW = 3         # Baja prioridad
    
    @property
    def label(self) -> str:
        """Etiqueta legible."""
        labels = {
            0: "Urgente",
            1: "Alta",
            2: "Media",
            3: "Baja"
        }
        return labels[self.value]
    
    @property
    def emoji(self) -> str:
        """Emoji representativo."""
        emojis = {
            0: "🔴",
            1: "🟠",
            2: "🟡",
            3: "🟢"
        }
        return emojis[self.value]


class TaskStatus(IntEnum):
    """Estados de una tarea."""
    PENDING = 0      # Pendiente
    IN_PROGRESS = 1  # En progreso
    COMPLETED = 2    # Completada
    CANCELLED = 3    # Cancelada
    
    @property
    def label(self) -> str:
        """Etiqueta legible."""
        labels = {
            0: "Pendiente",
            1: "En progreso",
            2: "Completada",
            3: "Cancelada"
        }
        return labels[self.value]
    
    @property
    def emoji(self) -> str:
        """Emoji representativo."""
        emojis = {
            0: "⏳",
            1: "🔄",
            2: "✅",
            3: "❌"
        }
        return emojis[self.value]


@dataclass
class Task:
    """
    Entidad de dominio: Tarea del estudiante.
    
    Representa una actividad académica o personal que el estudiante
    debe completar, con fecha límite y prioridad.
    """
    title: str
    description: str
    due_date: datetime
    priority: TaskPriority
    user_id: str
    status: TaskStatus = TaskStatus.PENDING
    category: str = "general"  # académico, personal, bienestar, etc.
    estimated_hours: float = 1.0
    completed_at: Optional[datetime] = None
    id: Optional[int] = None
    created_at: Optional[datetime] = None
    
    def __post_init__(self):
        """Validaciones de negocio."""
        if not self.title or len(self.title.strip()) == 0:
            raise ValueError("El título de la tarea no puede estar vacío")
        
        if len(self.title) > 200:
            raise ValueError("El título no puede exceder 200 caracteres")
        
        if len(self.description) > 1000:
            raise ValueError("La descripción no puede exceder 1000 caracteres")
        
        if self.estimated_hours <= 0:
            raise ValueError("Las horas estimadas deben ser positivas")
        
        if self.estimated_hours > 100:
            raise ValueError("Las horas estimadas no pueden exceder 100")
    
    @property
    def is_overdue(self) -> bool:
        """Indica si la tarea está vencida."""
        if self.status in [TaskStatus.COMPLETED, TaskStatus.CANCELLED]:
            return False
        return datetime.now() > self.due_date
    
    @property
    def days_until_due(self) -> int:
        """Días hasta la fecha límite (negativo si está vencida)."""
        delta = self.due_date - datetime.now()
        return delta.days
    
    @property
    def urgency_score(self) -> float:
        """
        Score de urgencia basado en prioridad y proximidad de fecha límite.
        Rango: 0.0 (nada urgente) a 10.0 (extremadamente urgente)
        """
        # Factor de prioridad (0.0 a 4.0)
        priority_weight = {
            TaskPriority.URGENT: 4.0,
            TaskPriority.HIGH: 3.0,
            TaskPriority.MEDIUM: 2.0,
            TaskPriority.LOW: 1.0
        }
        priority_score = priority_weight.get(self.priority, 1.0)
        
        # Factor de tiempo (0.0 a 6.0)
        days = self.days_until_due
        if days < 0:
            time_score = 6.0  # Vencida
        elif days == 0:
            time_score = 5.5  # Hoy
        elif days == 1:
            time_score = 5.0  # Mañana
        elif days <= 3:
            time_score = 4.0
        elif days <= 7:
            time_score = 3.0
        elif days <= 14:
            time_score = 2.0
        else:
            time_score = 1.0
        
        return priority_score + time_score


@dataclass
class Reminder:
    """
    Entidad de dominio: Recordatorio de tarea.
    
    Notificación programada para recordar al estudiante sobre una tarea.
    """
    task_id: int
    remind_at: datetime
    message: str = ""
    is_sent: bool = False
    id: Optional[int] = None
    created_at: Optional[datetime] = None
    
    def __post_init__(self):
        """Validaciones."""
        if self.remind_at < datetime.now() - timedelta(hours=1):
            raise ValueError("La fecha de recordatorio no puede estar muy en el pasado")


@dataclass
class TaskStatistics:
    """
    Estadísticas de tareas de un usuario en un período.
    """
    user_id: str
    period_start: datetime
    period_end: datetime
    total_tasks: int
    completed_tasks: int
    pending_tasks: int
    overdue_tasks: int
    completion_rate: float  # 0.0 a 1.0
    avg_completion_time_hours: float
    tasks_by_priority: dict[str, int]
    tasks_by_category: dict[str, int]
    productivity_trend: str  # "mejorando", "estable", "decayendo"
    
    @property
    def completion_percentage(self) -> float:
        """Porcentaje de tareas completadas."""
        return self.completion_rate * 100


@dataclass
class TaskSuggestion:
    """
    Sugerencia de priorización generada por IA.
    """
    task_id: int
    suggested_priority: TaskPriority
    reasoning: str
    confidence: float  # 0.0 a 1.0
    tips: List[str] = field(default_factory=list)


@dataclass
class DailySchedule:
    """
    Agenda diaria sugerida por el planificador inteligente.
    """
    date: date
    tasks: List[Task]
    total_estimated_hours: float
    is_feasible: bool
    recommendations: List[str] = field(default_factory=list)
    
    @property
    def is_overloaded(self) -> bool:
        """Indica si la carga diaria es excesiva (>8 horas)."""
        return self.total_estimated_hours > 8.0
