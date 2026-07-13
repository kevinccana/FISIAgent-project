"""
Casos de uso para el Dashboard de Bienestar
"""
import logging
from datetime import datetime, timedelta
from typing import List
from app.core.domain.mood_models import (
    MoodEntry, MoodLevel, MoodStatistics, MonthlyMoodSummary, DailyMoodEntry
)
from app.core.domain.agent import AgentTask, AgentRole
from app.ports.outbound.mood_repository import MoodLogRepositoryPort

logger = logging.getLogger(__name__)


class RegisterMoodUseCase:
    """
    Caso de uso: Registrar el estado de ánimo del usuario.
    
    Validaciones del dominio:
    - Mood debe ser válido (0-3)
    - Nota no debe exceder 500 caracteres
    """
    
    def __init__(self, mood_repository: MoodLogRepositoryPort):
        self.mood_repository = mood_repository
    
    def execute(
        self,
        user_id: str,
        mood: MoodLevel,
        note: str = "",
        timestamp: datetime = None
    ) -> MoodEntry:
        """
        Registra un nuevo estado de ánimo.
        
        Args:
            user_id: ID del usuario
            mood: Nivel de ánimo (MoodLevel)
            note: Nota opcional (máx 500 chars)
            timestamp: Momento del registro (default: ahora)
            
        Returns:
            MoodEntry guardado con ID asignado
        """
        if timestamp is None:
            timestamp = datetime.now()
        
        # Crear entrada de dominio (valida automáticamente)
        mood_entry = MoodEntry(
            id=None,
            user_id=user_id,
            mood=mood,
            note=note.strip(),
            timestamp=timestamp
        )
        
        # Persistir
        saved_entry = self.mood_repository.save_mood(mood_entry)
        
        logger.info(f"Mood registrado: user={user_id}, mood={mood.label}, id={saved_entry.id}")
        return saved_entry


class GetMoodHistoryUseCase:
    """
    Caso de uso: Obtener historial de registros de ánimo.
    """
    
    def __init__(self, mood_repository: MoodLogRepositoryPort):
        self.mood_repository = mood_repository
    
    def execute(
        self,
        user_id: str,
        days: int = 30,
        limit: int = None
    ) -> List[MoodEntry]:
        """
        Obtiene registros de ánimo recientes.
        
        Args:
            user_id: ID del usuario
            days: Número de días hacia atrás (default: 30)
            limit: Límite máximo de resultados
            
        Returns:
            Lista de MoodEntry ordenados por fecha DESC
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        entries = self.mood_repository.get_user_moods(
            user_id=user_id,
            start_date=start_date,
            end_date=end_date,
            limit=limit
        )
        
        logger.info(f"Recuperados {len(entries)} mood entries para user={user_id}")
        return entries


class GetMonthlyCalendarUseCase:
    """
    Caso de uso: Obtener calendario mensual de estados de ánimo.
    
    Usado por el frontend para renderizar el calendario con colores.
    """
    
    def __init__(self, mood_repository: MoodLogRepositoryPort):
        self.mood_repository = mood_repository
    
    def execute(self, user_id: str, year: int, month: int) -> dict:
        """
        Obtiene datos para el calendario mensual.
        
        Args:
            user_id: ID del usuario
            year: Año (ej: 2026)
            month: Mes (1-12)
            
        Returns:
            Dict con estructura:
            {
                "year": 2026,
                "month": 7,
                "entries": {
                    1: {"mood": 0, "note": "Muy buen día"},
                    5: {"mood": 2, "note": "Estresante"},
                    ...
                }
            }
        """
        daily_entries = self.mood_repository.get_monthly_calendar(user_id, year, month)
        
        # Convertir a formato del frontend
        entries_dict = {}
        for entry in daily_entries:
            entries_dict[entry.day] = {
                "mood": entry.mood.value,
                "note": entry.note
            }
        
        logger.info(f"Calendario mensual: user={user_id}, {year}-{month:02d}, {len(entries_dict)} días")
        
        return {
            "year": year,
            "month": month,
            "entries": entries_dict
        }


class GetMoodInsightsUseCase:
    """
    Caso de uso: Generar insights sobre el estado emocional.
    
    Combina estadísticas con análisis de patrones.
    """
    
    def __init__(self, mood_repository: MoodLogRepositoryPort):
        self.mood_repository = mood_repository
    
    def execute(self, user_id: str, days: int = 30) -> dict:
        """
        Genera insights sobre el estado emocional del usuario.
        
        Args:
            user_id: ID del usuario
            days: Período de análisis (default: últimos 30 días)
            
        Returns:
            Dict con insights:
            {
                "statistics": MoodStatistics,
                "monthly_history": List[MonthlyMoodSummary],
                "insights": List[str],
                "recommendations": List[str]
            }
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Obtener estadísticas del período
        statistics = self.mood_repository.get_statistics(user_id, start_date, end_date)
        
        # Obtener historial mensual (últimos 6 meses)
        monthly_history = self.mood_repository.get_monthly_history(user_id, months=6)
        
        # Generar insights textuales
        insights = self._generate_insights(statistics, monthly_history)
        
        # Generar recomendaciones
        recommendations = self._generate_recommendations(statistics)
        
        return {
            "statistics": statistics,
            "monthly_history": monthly_history,
            "insights": insights,
            "recommendations": recommendations
        }
    
    def _generate_insights(
        self,
        stats: MoodStatistics,
        history: List[MonthlyMoodSummary]
    ) -> List[str]:
        """Genera insights textuales basados en datos."""
        insights = []
        
        if stats.total_entries == 0:
            insights.append("Aún no tienes suficientes registros para generar insights.")
            return insights
        
        # Insight sobre tendencia general
        if stats.mood_trend == "positivo":
            insights.append(f"🎉 Tu estado de ánimo ha sido mayormente positivo (promedio: {stats.avg_mood:.1f}/3.0)")
        elif stats.mood_trend == "neutral":
            insights.append(f"📊 Tu estado de ánimo ha sido equilibrado (promedio: {stats.avg_mood:.1f}/3.0)")
        else:
            insights.append(f"⚠️ Has tenido varios días difíciles (promedio: {stats.avg_mood:.1f}/3.0)")
        
        # Insight sobre consistencia
        most_common = stats.most_common_mood
        frequency = stats.mood_distribution.get(most_common, 0)
        percentage = (frequency / stats.total_entries) * 100
        insights.append(f"Tu estado más frecuente es '{most_common.label}' ({percentage:.0f}% del tiempo)")
        
        # Insight sobre días difíciles
        bad_days = stats.mood_distribution.get(MoodLevel.MUY_MAL, 0)
        if bad_days > 0:
            insights.append(f"Tuviste {bad_days} días especialmente difíciles. Recuerda que está bien pedir ayuda.")
        
        # Insight sobre evolución (si hay historial)
        if len(history) >= 2:
            last_month = history[-1].avg_mood
            prev_month = history[-2].avg_mood
            diff = prev_month - last_month  # positivo = mejora (valores bajos = mejor)
            
            if diff > 0.3:
                insights.append(f"📈 Tu ánimo ha mejorado respecto al mes anterior (+{diff:.1f} puntos)")
            elif diff < -0.3:
                insights.append(f"📉 Tu ánimo ha disminuido respecto al mes anterior ({diff:.1f} puntos)")
        
        return insights
    
    def _generate_recommendations(self, stats: MoodStatistics) -> List[str]:
        """Genera recomendaciones basadas en estadísticas."""
        recommendations = []
        
        if stats.total_entries == 0:
            recommendations.append("Comienza a registrar tu ánimo diariamente para obtener recomendaciones personalizadas.")
            return recommendations
        
        # Recomendaciones según tendencia
        if stats.mood_trend == "negativo":
            recommendations.append("Considera hablar con un profesional de salud mental de la Oficina de Bienestar Estudiantil.")
            recommendations.append("Prueba técnicas de relajación como respiración profunda o mindfulness.")
        
        # Recomendaciones según días muy malos
        very_bad_days = stats.mood_distribution.get(MoodLevel.MUY_MAL, 0)
        if very_bad_days >= 3:
            recommendations.append("Has tenido varios días muy difíciles. No estás solo: contacta a la Línea 113 (opción 5) - 24/7 gratuito.")
        
        # Recomendaciones generales
        if stats.avg_mood > 1.5:
            recommendations.append("Intenta establecer una rutina de sueño regular y hacer ejercicio moderado.")
            recommendations.append("Conéctate con amigos o familiares - el apoyo social es fundamental.")
        
        if stats.total_entries < 10:
            recommendations.append("Sigue registrando tu ánimo para que podamos darte mejores recomendaciones.")
        
        return recommendations


class GetMoodAIInsightsUseCase:
    """
    Caso de uso: Generar un análisis elaborado del estado de ánimo con IA.

    A diferencia de GetMoodInsightsUseCase (reglas fijas, siempre disponible),
    este delega en MoodInsightsAgent (Gemini) para un diagnóstico narrativo,
    recomendaciones desarrolladas y recursos para investigar. Es opt-in -- se
    dispara desde un botón aparte en el frontend, no en cada carga de página.
    """

    def __init__(self, mood_repository: MoodLogRepositoryPort, mood_insights_agent):
        self.mood_repository = mood_repository
        self.mood_insights_agent = mood_insights_agent

    async def execute(self, user_id: str, days: int = 30) -> dict:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        statistics = self.mood_repository.get_statistics(user_id, start_date, end_date)
        monthly_history = self.mood_repository.get_monthly_history(user_id, months=6)
        entries = self.mood_repository.get_user_moods(user_id, start_date, end_date, limit=30)

        agent_task = AgentTask(
            agent_role=AgentRole.MOOD_ANALYST,
            input_data={
                "statistics": statistics,
                "monthly_history": monthly_history,
                "entries": entries,
            }
        )

        result = await self.mood_insights_agent.execute(agent_task)

        if result.success:
            return result.data

        logger.warning(f"MoodInsightsAgent falló para user={user_id}: {result.error_message}")
        return {
            "diagnosis": "No se pudo generar el análisis con IA en este momento. Intenta de nuevo más tarde.",
            "recommendations": [],
            "resources": [],
        }


class UpdateMoodUseCase:
    """Caso de uso: Actualizar un registro existente."""
    
    def __init__(self, mood_repository: MoodLogRepositoryPort):
        self.mood_repository = mood_repository
    
    def execute(self, entry_id: int, mood: MoodLevel, note: str) -> bool:
        """
        Actualiza un registro de ánimo.
        
        Args:
            entry_id: ID del registro
            mood: Nuevo nivel de ánimo
            note: Nueva nota
            
        Returns:
            True si se actualizó, False si no existe
        """
        # Obtener registro existente
        existing = self.mood_repository.get_mood_by_id(entry_id)
        if not existing:
            logger.warning(f"Intento de actualizar mood inexistente: id={entry_id}")
            return False
        
        # Actualizar campos
        existing.mood = mood
        existing.note = note.strip()
        
        # Persistir
        updated = self.mood_repository.update_mood(existing)
        
        if updated:
            logger.info(f"Mood actualizado: id={entry_id}, mood={mood.label}")
        
        return updated


class DeleteMoodUseCase:
    """Caso de uso: Eliminar un registro."""
    
    def __init__(self, mood_repository: MoodLogRepositoryPort):
        self.mood_repository = mood_repository
    
    def execute(self, entry_id: int) -> bool:
        """
        Elimina un registro de ánimo.
        
        Args:
            entry_id: ID del registro
            
        Returns:
            True si se eliminó, False si no existía
        """
        deleted = self.mood_repository.delete_mood(entry_id)
        
        if deleted:
            logger.info(f"Mood eliminado: id={entry_id}")
        else:
            logger.warning(f"Intento de eliminar mood inexistente: id={entry_id}")
        
        return deleted
