"""
Router API para Dashboard de Bienestar (Mood Logs)

Adapter de entrada (Hexagonal Architecture) que expone casos de uso como endpoints HTTP.
"""
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from app.core.domain.mood_models import MoodLevel, MoodStatistics, MonthlyMoodSummary
from app.core.use_cases.mood_use_cases import (
    RegisterMoodUseCase,
    GetMoodHistoryUseCase,
    GetMonthlyCalendarUseCase,
    GetMoodInsightsUseCase,
    UpdateMoodUseCase,
    DeleteMoodUseCase
)

router = APIRouter(prefix="/mood", tags=["Dashboard de Bienestar"])

# ═══════════════════════════════════════════════════════════════════════════════
# DTOs (Data Transfer Objects) - Modelos Pydantic para la API
# ═══════════════════════════════════════════════════════════════════════════════

class RegisterMoodDTO(BaseModel):
    """DTO para registrar un nuevo estado de ánimo."""
    user_id: str = Field(..., description="ID del usuario (temporal, hasta tener auth)")
    mood: int = Field(..., ge=0, le=3, description="Nivel de ánimo: 0=Muy bien, 1=Bien, 2=Mal, 3=Muy mal")
    note: str = Field(default="", max_length=500, description="Nota opcional del usuario")
    
    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "estudiante_123",
                "mood": 1,
                "note": "Día tranquilo y productivo"
            }
        }


class MoodEntryDTO(BaseModel):
    """DTO para un registro de ánimo."""
    id: int
    user_id: str
    mood: int
    mood_label: str
    note: str
    timestamp: datetime
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": 1,
                "user_id": "estudiante_123",
                "mood": 1,
                "mood_label": "Bien",
                "note": "Día tranquilo",
                "timestamp": "2026-07-08T14:30:00"
            }
        }


class MonthlyCalendarDTO(BaseModel):
    """DTO para calendario mensual."""
    year: int
    month: int
    entries: dict  # {day: {mood: int, note: str}}
    
    class Config:
        json_schema_extra = {
            "example": {
                "year": 2026,
                "month": 7,
                "entries": {
                    "1": {"mood": 0, "note": "Gran día"},
                    "5": {"mood": 2, "note": "Estresante"}
                }
            }
        }


class MonthlyHistoryItemDTO(BaseModel):
    """DTO para un ítem del historial mensual."""
    year: int
    month: int
    month_label: str
    avg_mood: float
    entry_count: int


class StatisticsDTO(BaseModel):
    """DTO para estadísticas de ánimo."""
    period_start: datetime
    period_end: datetime
    total_entries: int
    avg_mood: float
    mood_distribution: dict
    most_common_mood: str
    mood_trend: str


class InsightsDTO(BaseModel):
    """DTO para insights del usuario."""
    statistics: StatisticsDTO
    monthly_history: List[MonthlyHistoryItemDTO]
    insights: List[str]
    recommendations: List[str]


class UpdateMoodDTO(BaseModel):
    """DTO para actualizar un registro."""
    mood: int = Field(..., ge=0, le=3)
    note: str = Field(default="", max_length=500)


# ═══════════════════════════════════════════════════════════════════════════════
# Dependency Injection - Los use cases se inyectan desde main.py
# ═══════════════════════════════════════════════════════════════════════════════

_register_mood_use_case: Optional[RegisterMoodUseCase] = None
_get_mood_history_use_case: Optional[GetMoodHistoryUseCase] = None
_get_monthly_calendar_use_case: Optional[GetMonthlyCalendarUseCase] = None
_get_mood_insights_use_case: Optional[GetMoodInsightsUseCase] = None
_update_mood_use_case: Optional[UpdateMoodUseCase] = None
_delete_mood_use_case: Optional[DeleteMoodUseCase] = None


def configure_mood_router(
    register_mood: RegisterMoodUseCase,
    get_history: GetMoodHistoryUseCase,
    get_calendar: GetMonthlyCalendarUseCase,
    get_insights: GetMoodInsightsUseCase,
    update_mood: UpdateMoodUseCase,
    delete_mood: DeleteMoodUseCase
):
    """Configura el router con los casos de uso (DI desde main.py)."""
    global _register_mood_use_case, _get_mood_history_use_case
    global _get_monthly_calendar_use_case, _get_mood_insights_use_case
    global _update_mood_use_case, _delete_mood_use_case
    
    _register_mood_use_case = register_mood
    _get_mood_history_use_case = get_history
    _get_monthly_calendar_use_case = get_calendar
    _get_mood_insights_use_case = get_insights
    _update_mood_use_case = update_mood
    _delete_mood_use_case = delete_mood


# ═══════════════════════════════════════════════════════════════════════════════
# Endpoints
# ═══════════════════════════════════════════════════════════════════════════════

@router.post("/register", response_model=MoodEntryDTO, status_code=status.HTTP_201_CREATED)
async def register_mood(dto: RegisterMoodDTO):
    """
    Registra un nuevo estado de ánimo.
    
    - **user_id**: ID del usuario (temporal, hasta implementar auth)
    - **mood**: 0=Muy bien, 1=Bien, 2=Mal, 3=Muy mal
    - **note**: Nota opcional (máx 500 caracteres)
    """
    if not _register_mood_use_case:
        raise HTTPException(status_code=500, detail="Servicio no inicializado")
    
    try:
        mood_level = MoodLevel(dto.mood)
    except ValueError:
        raise HTTPException(status_code=400, detail="Mood inválido (debe ser 0-3)")
    
    mood_entry = _register_mood_use_case.execute(
        user_id=dto.user_id,
        mood=mood_level,
        note=dto.note
    )
    
    return MoodEntryDTO(
        id=mood_entry.id,
        user_id=mood_entry.user_id,
        mood=mood_entry.mood.value,
        mood_label=mood_entry.mood.label,
        note=mood_entry.note,
        timestamp=mood_entry.timestamp
    )


@router.get("/history/{user_id}", response_model=List[MoodEntryDTO])
async def get_mood_history(user_id: str, days: int = 30, limit: Optional[int] = None):
    """
    Obtiene el historial de registros de ánimo.
    
    - **user_id**: ID del usuario
    - **days**: Número de días hacia atrás (default: 30)
    - **limit**: Límite máximo de resultados
    """
    if not _get_mood_history_use_case:
        raise HTTPException(status_code=500, detail="Servicio no inicializado")
    
    entries = _get_mood_history_use_case.execute(user_id, days, limit)
    
    return [
        MoodEntryDTO(
            id=entry.id,
            user_id=entry.user_id,
            mood=entry.mood.value,
            mood_label=entry.mood.label,
            note=entry.note,
            timestamp=entry.timestamp
        )
        for entry in entries
    ]


@router.get("/calendar/{user_id}/{year}/{month}", response_model=MonthlyCalendarDTO)
async def get_monthly_calendar(user_id: str, year: int, month: int):
    """
    Obtiene el calendario mensual de estados de ánimo.
    
    - **user_id**: ID del usuario
    - **year**: Año (ej: 2026)
    - **month**: Mes (1-12)
    
    Retorna un diccionario con entradas por día del mes.
    """
    if not _get_monthly_calendar_use_case:
        raise HTTPException(status_code=500, detail="Servicio no inicializado")
    
    if not (1 <= month <= 12):
        raise HTTPException(status_code=400, detail="Mes inválido (debe ser 1-12)")
    
    calendar_data = _get_monthly_calendar_use_case.execute(user_id, year, month)
    return MonthlyCalendarDTO(**calendar_data)


@router.get("/insights/{user_id}", response_model=InsightsDTO)
async def get_mood_insights(user_id: str, days: int = 30):
    """
    Genera insights sobre el estado emocional del usuario.
    
    - **user_id**: ID del usuario
    - **days**: Período de análisis (default: 30 días)
    
    Retorna estadísticas, historial mensual, insights y recomendaciones.
    """
    if not _get_mood_insights_use_case:
        raise HTTPException(status_code=500, detail="Servicio no inicializado")
    
    insights_data = _get_mood_insights_use_case.execute(user_id, days)
    
    # Convertir MoodStatistics a DTO
    stats = insights_data["statistics"]
    stats_dto = StatisticsDTO(
        period_start=stats.period_start,
        period_end=stats.period_end,
        total_entries=stats.total_entries,
        avg_mood=stats.avg_mood,
        mood_distribution={k.label: v for k, v in stats.mood_distribution.items()},
        most_common_mood=stats.most_common_mood.label,
        mood_trend=stats.mood_trend
    )
    
    # Convertir MonthlyMoodSummary a DTO
    history_dto = [
        MonthlyHistoryItemDTO(
            year=item.year,
            month=item.month,
            month_label=item.month_label,
            avg_mood=item.avg_mood,
            entry_count=item.entry_count
        )
        for item in insights_data["monthly_history"]
    ]
    
    return InsightsDTO(
        statistics=stats_dto,
        monthly_history=history_dto,
        insights=insights_data["insights"],
        recommendations=insights_data["recommendations"]
    )


@router.put("/{entry_id}", status_code=status.HTTP_200_OK)
async def update_mood(entry_id: int, dto: UpdateMoodDTO):
    """
    Actualiza un registro de ánimo existente.
    
    - **entry_id**: ID del registro a actualizar
    - **mood**: Nuevo nivel de ánimo (0-3)
    - **note**: Nueva nota
    """
    if not _update_mood_use_case:
        raise HTTPException(status_code=500, detail="Servicio no inicializado")
    
    try:
        mood_level = MoodLevel(dto.mood)
    except ValueError:
        raise HTTPException(status_code=400, detail="Mood inválido (debe ser 0-3)")
    
    updated = _update_mood_use_case.execute(entry_id, mood_level, dto.note)
    
    if not updated:
        raise HTTPException(status_code=404, detail="Registro no encontrado")
    
    return {"message": "Registro actualizado correctamente", "id": entry_id}


@router.delete("/{entry_id}", status_code=status.HTTP_200_OK)
async def delete_mood(entry_id: int):
    """
    Elimina un registro de ánimo.
    
    - **entry_id**: ID del registro a eliminar
    """
    if not _delete_mood_use_case:
        raise HTTPException(status_code=500, detail="Servicio no inicializado")
    
    deleted = _delete_mood_use_case.execute(entry_id)
    
    if not deleted:
        raise HTTPException(status_code=404, detail="Registro no encontrado")
    
    return {"message": "Registro eliminado correctamente", "id": entry_id}
