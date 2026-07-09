"""
Port (contrato) para el repositorio de tareas.

Funcionalidad 3: Define la interfaz para persistir y recuperar tareas,
independiente de la tecnología de almacenamiento.
"""

from abc import ABC, abstractmethod
from datetime import datetime, date
from typing import List, Optional
from app.core.domain.task_models import Task, Reminder, TaskStatistics, TaskStatus, TaskPriority


class TaskRepositoryPort(ABC):
    """
    Contrato para repositorios de tareas.
    
    Arquitectura Hexagonal: Este port define las operaciones necesarias
    sin acoplarse a ninguna tecnología específica (SQLite, PostgreSQL, etc.)
    """
    
    @abstractmethod
    def save_task(self, task: Task) -> Task:
        """
        Persiste una nueva tarea.
        
        Args:
            task: Tarea a guardar
        
        Returns:
            Tarea guardada con ID asignado
        """
        pass
    
    @abstractmethod
    def get_task_by_id(self, task_id: int) -> Optional[Task]:
        """
        Recupera una tarea por su ID.
        
        Args:
            task_id: ID de la tarea
        
        Returns:
            Tarea encontrada o None
        """
        pass
    
    @abstractmethod
    def get_user_tasks(
        self,
        user_id: str,
        status: Optional[TaskStatus] = None,
        priority: Optional[TaskPriority] = None,
        category: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[Task]:
        """
        Recupera tareas de un usuario con filtros opcionales.
        
        Args:
            user_id: ID del usuario
            status: Filtro por estado (opcional)
            priority: Filtro por prioridad (opcional)
            category: Filtro por categoría (opcional)
            limit: Límite de resultados (opcional)
        
        Returns:
            Lista de tareas
        """
        pass
    
    @abstractmethod
    def get_upcoming_tasks(
        self,
        user_id: str,
        days_ahead: int = 7,
        limit: Optional[int] = None
    ) -> List[Task]:
        """
        Recupera tareas próximas por vencer.
        
        Args:
            user_id: ID del usuario
            days_ahead: Días hacia adelante a considerar
            limit: Límite de resultados
        
        Returns:
            Lista de tareas ordenadas por urgencia
        """
        pass
    
    @abstractmethod
    def get_overdue_tasks(self, user_id: str) -> List[Task]:
        """
        Recupera tareas vencidas del usuario.
        
        Args:
            user_id: ID del usuario
        
        Returns:
            Lista de tareas vencidas
        """
        pass
    
    @abstractmethod
    def get_tasks_for_date(self, user_id: str, target_date: date) -> List[Task]:
        """
        Recupera tareas para una fecha específica.
        
        Args:
            user_id: ID del usuario
            target_date: Fecha objetivo
        
        Returns:
            Lista de tareas para esa fecha
        """
        pass
    
    @abstractmethod
    def update_task(self, task: Task) -> Task:
        """
        Actualiza una tarea existente.
        
        Args:
            task: Tarea con cambios
        
        Returns:
            Tarea actualizada
        """
        pass
    
    @abstractmethod
    def delete_task(self, task_id: int) -> bool:
        """
        Elimina una tarea.
        
        Args:
            task_id: ID de la tarea
        
        Returns:
            True si se eliminó correctamente
        """
        pass
    
    @abstractmethod
    def get_statistics(
        self,
        user_id: str,
        start_date: datetime,
        end_date: datetime
    ) -> TaskStatistics:
        """
        Calcula estadísticas de tareas en un período.
        
        Args:
            user_id: ID del usuario
            start_date: Inicio del período
            end_date: Fin del período
        
        Returns:
            Estadísticas calculadas
        """
        pass
    
    @abstractmethod
    def save_reminder(self, reminder: Reminder) -> Reminder:
        """
        Guarda un recordatorio para una tarea.
        
        Args:
            reminder: Recordatorio a guardar
        
        Returns:
            Recordatorio guardado con ID
        """
        pass
    
    @abstractmethod
    def get_pending_reminders(self, before: datetime) -> List[Reminder]:
        """
        Recupera recordatorios pendientes de enviar.
        
        Args:
            before: Fecha límite (recordatorios programados antes de esta fecha)
        
        Returns:
            Lista de recordatorios pendientes
        """
        pass
