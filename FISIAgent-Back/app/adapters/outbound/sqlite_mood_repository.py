"""
SQLiteMoodLogRepository - Implementación de repositorio con SQLite

Implementa el MoodLogRepositoryPort usando SQLite como base de datos.
Base de datos ligera, sin servidor, ideal para desarrollo y producción pequeña.
"""
import sqlite3
import logging
from pathlib import Path
from typing import List, Optional
from datetime import datetime, timedelta
from app.ports.outbound.mood_repository import MoodLogRepositoryPort
from app.core.domain.mood_models import (
    MoodEntry, MoodLevel, MoodStatistics, MonthlyMoodSummary, DailyMoodEntry
)

logger = logging.getLogger(__name__)


class SQLiteMoodLogRepository(MoodLogRepositoryPort):
    """
    Adapter que implementa persistencia de mood logs con SQLite.
    
    Características:
    - Base de datos en archivo (fisiagent.db)
    - Thread-safe con check_same_thread=False
    - Auto-inicialización de tabla
    - Índices para consultas rápidas
    """
    
    def __init__(self, db_path: str = "fisiagent.db"):
        """
        Inicializa el repositorio SQLite.
        
        Args:
            db_path: Ruta al archivo de base de datos
        """
        self.db_path = db_path
        self._init_database()
        logger.info(f"SQLiteMoodLogRepository inicializado: {db_path}")
    
    def _init_database(self):
        """Crea la tabla si no existe."""
        with sqlite3.connect(self.db_path, check_same_thread=False) as conn:
            cursor = conn.cursor()
            
            # Tabla principal
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS mood_entries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    mood INTEGER NOT NULL,
                    note TEXT NOT NULL DEFAULT '',
                    timestamp TEXT NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Índices para consultas rápidas
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_user_timestamp 
                ON mood_entries(user_id, timestamp DESC)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_user_month
                ON mood_entries(user_id, strftime('%Y-%m', timestamp))
            """)
            
            conn.commit()
            logger.info("Base de datos mood_entries inicializada")
    
    def _get_connection(self):
        """Crea una conexión a la base de datos."""
        return sqlite3.connect(self.db_path, check_same_thread=False)
    
    def save_mood(self, mood_entry: MoodEntry) -> MoodEntry:
        """Guarda un nuevo registro de ánimo."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO mood_entries (user_id, mood, note, timestamp)
                VALUES (?, ?, ?, ?)
            """, (
                mood_entry.user_id,
                mood_entry.mood.value,
                mood_entry.note,
                mood_entry.timestamp.isoformat()
            ))
            conn.commit()
            entry_id = cursor.lastrowid
            
            logger.info(f"Mood guardado: user={mood_entry.user_id}, mood={mood_entry.mood.label}, id={entry_id}")
            
            # Retornar con ID asignado
            return MoodEntry(
                id=entry_id,
                user_id=mood_entry.user_id,
                mood=mood_entry.mood,
                note=mood_entry.note,
                timestamp=mood_entry.timestamp
            )
    
    def get_mood_by_id(self, entry_id: int) -> Optional[MoodEntry]:
        """Recupera un registro por ID."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, user_id, mood, note, timestamp
                FROM mood_entries
                WHERE id = ?
            """, (entry_id,))
            row = cursor.fetchone()
            
            if not row:
                return None
            
            return self._row_to_mood_entry(row)
    
    def get_user_moods(
        self,
        user_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: Optional[int] = None
    ) -> List[MoodEntry]:
        """Recupera registros de un usuario con filtros opcionales."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            query = """
                SELECT id, user_id, mood, note, timestamp
                FROM mood_entries
                WHERE user_id = ?
            """
            params = [user_id]
            
            if start_date:
                query += " AND timestamp >= ?"
                params.append(start_date.isoformat())
            
            if end_date:
                query += " AND timestamp <= ?"
                params.append(end_date.isoformat())
            
            query += " ORDER BY timestamp DESC"
            
            if limit:
                query += " LIMIT ?"
                params.append(limit)
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            return [self._row_to_mood_entry(row) for row in rows]
    
    def get_monthly_calendar(
        self,
        user_id: str,
        year: int,
        month: int
    ) -> List[DailyMoodEntry]:
        """Recupera todos los registros de un mes para el calendario."""
        # Calcular primer y último día del mes
        start_date = datetime(year, month, 1)
        if month == 12:
            end_date = datetime(year + 1, 1, 1) - timedelta(seconds=1)
        else:
            end_date = datetime(year, month + 1, 1) - timedelta(seconds=1)
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT strftime('%d', timestamp) as day, mood, note
                FROM mood_entries
                WHERE user_id = ?
                  AND timestamp >= ?
                  AND timestamp <= ?
                ORDER BY timestamp DESC
            """, (user_id, start_date.isoformat(), end_date.isoformat()))
            
            rows = cursor.fetchall()
            
            # Convertir a DailyMoodEntry
            # Si hay múltiples registros en un día, tomamos el más reciente
            daily_entries = {}
            for row in rows:
                day = int(row[0])
                if day not in daily_entries:
                    daily_entries[day] = DailyMoodEntry(
                        day=day,
                        mood=MoodLevel(row[1]),
                        note=row[2]
                    )
            
            return list(daily_entries.values())
    
    def get_monthly_history(
        self,
        user_id: str,
        months: int = 6
    ) -> List[MonthlyMoodSummary]:
        """Recupera resumen mensual de los últimos N meses."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Fecha límite (N meses atrás)
            limit_date = datetime.now() - timedelta(days=months * 30)
            
            cursor.execute("""
                SELECT 
                    strftime('%Y', timestamp) as year,
                    strftime('%m', timestamp) as month,
                    AVG(mood) as avg_mood,
                    COUNT(*) as entry_count
                FROM mood_entries
                WHERE user_id = ?
                  AND timestamp >= ?
                GROUP BY year, month
                ORDER BY year, month
            """, (user_id, limit_date.isoformat()))
            
            rows = cursor.fetchall()
            
            return [
                MonthlyMoodSummary(
                    year=int(row[0]),
                    month=int(row[1]),
                    avg_mood=round(row[2], 2),
                    entry_count=row[3]
                )
                for row in rows
            ]
    
    def get_statistics(
        self,
        user_id: str,
        start_date: datetime,
        end_date: datetime
    ) -> MoodStatistics:
        """Calcula estadísticas para un período."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Obtener todos los registros del período
            cursor.execute("""
                SELECT mood
                FROM mood_entries
                WHERE user_id = ?
                  AND timestamp >= ?
                  AND timestamp <= ?
            """, (user_id, start_date.isoformat(), end_date.isoformat()))
            
            moods = [MoodLevel(row[0]) for row in cursor.fetchall()]
            
            if not moods:
                # Sin datos, retornar estadísticas vacías
                return MoodStatistics(
                    period_start=start_date,
                    period_end=end_date,
                    total_entries=0,
                    avg_mood=0.0,
                    mood_distribution={},
                    most_common_mood=MoodLevel.BIEN
                )
            
            # Calcular distribución
            distribution = {level: moods.count(level) for level in MoodLevel}
            most_common = max(distribution, key=distribution.get)
            avg = sum(m.value for m in moods) / len(moods)
            
            return MoodStatistics(
                period_start=start_date,
                period_end=end_date,
                total_entries=len(moods),
                avg_mood=round(avg, 2),
                mood_distribution=distribution,
                most_common_mood=most_common
            )
    
    def update_mood(self, mood_entry: MoodEntry) -> bool:
        """Actualiza un registro existente."""
        if mood_entry.id is None:
            return False
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE mood_entries
                SET mood = ?, note = ?, timestamp = ?
                WHERE id = ?
            """, (
                mood_entry.mood.value,
                mood_entry.note,
                mood_entry.timestamp.isoformat(),
                mood_entry.id
            ))
            conn.commit()
            
            updated = cursor.rowcount > 0
            if updated:
                logger.info(f"Mood actualizado: id={mood_entry.id}")
            
            return updated
    
    def delete_mood(self, entry_id: int) -> bool:
        """Elimina un registro."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM mood_entries WHERE id = ?", (entry_id,))
            conn.commit()
            
            deleted = cursor.rowcount > 0
            if deleted:
                logger.info(f"Mood eliminado: id={entry_id}")
            
            return deleted
    
    def _row_to_mood_entry(self, row) -> MoodEntry:
        """Convierte una fila de SQLite a MoodEntry."""
        return MoodEntry(
            id=row[0],
            user_id=row[1],
            mood=MoodLevel(row[2]),
            note=row[3],
            timestamp=datetime.fromisoformat(row[4])
        )
