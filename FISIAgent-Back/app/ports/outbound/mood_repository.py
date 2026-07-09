"""
MoodLogRepositoryPort - Contrato para repositorio de registros de ánimo

Define las operaciones de persistencia sin conocer la tecnología específica
(SQLite, PostgreSQL, MongoDB, etc.).
"""
from abc import ABC, abstractmethod
from typing import List, Optional
from datetime import datetime
from app.core.domain.mood_models import MoodEntry, MoodStatistics, MonthlyMoodSummary, DailyMoodEntry


class MoodLogRepositoryPort(ABC):
    """
    Port de salida para persistencia de registros de ánimo.
    
    Cualquier implementación (SQLite, Postgres, etc.) debe cumplir este contrato.
    """
    
    @abstractmethod
    def save_mood(self, mood_entry: MoodEntry) -> MoodEntry:
        """
        Guarda un nuevo registro de ánimo.
        
        Args:
            mood_entry: Registro a guardar (id puede ser None)
            
        Returns:
            MoodEntry con id asignado
        """
        pass
    
    @abstractmethod
    def get_mood_by_id(self, entry_id: int) -> Optional[MoodEntry]:
        """
        Recupera un registro de ánimo por ID.
        
        Args:
            entry_id: ID del registro
            
        Returns:
            MoodEntry si existe, None si no
        """
        pass
    
    @abstractmethod
    def get_user_moods(
        self,
        user_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: Optional[int] = None
    ) -> List[MoodEntry]:
        """
        Recupera registros de ánimo de un usuario.
        
        Args:
            user_id: ID del usuario
            start_date: Fecha inicial (opcional, por defecto sin límite)
            end_date: Fecha final (opcional, por defecto ahora)
            limit: Número máximo de resultados (opcional)
            
        Returns:
            Lista de MoodEntry ordenados por timestamp DESC
        """
        pass
    
    @abstractmethod
    def get_monthly_calendar(
        self,
        user_id: str,
        year: int,
        month: int
    ) -> List[DailyMoodEntry]:
        """
        Recupera todos los registros de un mes específico para el calendario.
        
        Args:
            user_id: ID del usuario
            year: Año (ej: 2026)
            month: Mes (1-12)
            
        Returns:
            Lista de DailyMoodEntry (un registro por día)
        """
        pass
    
    @abstractmethod
    def get_monthly_history(
        self,
        user_id: str,
        months: int = 6
    ) -> List[MonthlyMoodSummary]:
        """
        Recupera resumen mensual de los últimos N meses.
        
        Args:
            user_id: ID del usuario
            months: Número de meses hacia atrás (default: 6)
            
        Returns:
            Lista de MonthlyMoodSummary ordenados cronológicamente
        """
        pass
    
    @abstractmethod
    def get_statistics(
        self,
        user_id: str,
        start_date: datetime,
        end_date: datetime
    ) -> MoodStatistics:
        """
        Calcula estadísticas de ánimo para un período.
        
        Args:
            user_id: ID del usuario
            start_date: Inicio del período
            end_date: Fin del período
            
        Returns:
            MoodStatistics con métricas agregadas
        """
        pass
    
    @abstractmethod
    def update_mood(self, mood_entry: MoodEntry) -> bool:
        """
        Actualiza un registro existente.
        
        Args:
            mood_entry: Registro con datos actualizados (debe tener id)
            
        Returns:
            True si se actualizó, False si no existe
        """
        pass
    
    @abstractmethod
    def delete_mood(self, entry_id: int) -> bool:
        """
        Elimina un registro de ánimo.
        
        Args:
            entry_id: ID del registro a eliminar
            
        Returns:
            True si se eliminó, False si no existía
        """
        pass
