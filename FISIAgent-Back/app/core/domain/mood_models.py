"""
Modelos de dominio para el Dashboard de Bienestar
"""
from dataclasses import dataclass
from datetime import datetime
from enum import IntEnum
from typing import Optional, List


class MoodLevel(IntEnum):
    """
    Niveles de ánimo (escala ordinal).
    
    Valores más bajos = mejor estado de ánimo.
    Alineado con el frontend: 0=Muy bien, 1=Bien, 2=Mal, 3=Muy mal
    """
    MUY_BIEN = 0
    BIEN = 1
    MAL = 2
    MUY_MAL = 3
    
    @property
    def label(self) -> str:
        """Etiqueta legible del nivel de ánimo."""
        labels = {
            MoodLevel.MUY_BIEN: "Muy bien",
            MoodLevel.BIEN: "Bien",
            MoodLevel.MAL: "Mal",
            MoodLevel.MUY_MAL: "Muy mal"
        }
        return labels[self]
    
    @property
    def emoji(self) -> str:
        """Emoji representativo."""
        emojis = {
            MoodLevel.MUY_BIEN: "😊",
            MoodLevel.BIEN: "🙂",
            MoodLevel.MAL: "😟",
            MoodLevel.MUY_MAL: "😢"
        }
        return emojis[self]


@dataclass
class MoodEntry:
    """
    Registro de ánimo de un usuario en un momento específico.
    
    Entidad del dominio (independiente de la infraestructura).
    """
    id: Optional[int]
    user_id: str  # Identificador del usuario (futuro: integrará con auth)
    mood: MoodLevel
    note: str  # Nota opcional del usuario
    timestamp: datetime
    
    def __post_init__(self):
        """Validaciones del dominio."""
        if not isinstance(self.mood, MoodLevel):
            raise ValueError(f"mood debe ser MoodLevel, recibido: {type(self.mood)}")
        if len(self.note) > 500:
            raise ValueError("La nota no puede exceder 500 caracteres")


@dataclass
class MoodStatistics:
    """
    Estadísticas agregadas de ánimo para un período.
    
    Value Object del dominio.
    """
    period_start: datetime
    period_end: datetime
    total_entries: int
    avg_mood: float  # Promedio numérico (0.0 - 3.0)
    mood_distribution: dict  # {MoodLevel.MUY_BIEN: 10, MoodLevel.BIEN: 5, ...}
    most_common_mood: MoodLevel
    
    @property
    def mood_trend(self) -> str:
        """
        Tendencia general del período.
        
        Returns:
            "positivo" si avg < 1.5, "neutral" si 1.5-2.0, "negativo" si > 2.0
        """
        if self.avg_mood < 1.5:
            return "positivo"
        elif self.avg_mood <= 2.0:
            return "neutral"
        else:
            return "negativo"


@dataclass
class MonthlyMoodSummary:
    """
    Resumen de ánimo por mes (para gráfico de línea).
    """
    year: int
    month: int  # 1-12
    avg_mood: float
    entry_count: int
    
    @property
    def month_label(self) -> str:
        """Etiqueta del mes (3 letras)."""
        months = ["Ene", "Feb", "Mar", "Abr", "May", "Jun",
                  "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]
        return months[self.month - 1]


@dataclass
class DailyMoodEntry:
    """
    Entrada de ánimo para un día específico (para calendario).
    """
    day: int  # 1-31
    mood: MoodLevel
    note: str
