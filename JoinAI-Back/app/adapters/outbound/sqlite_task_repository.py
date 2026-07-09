"""
Adapter SQLite para el repositorio de tareas.

Funcionalidad 3: Implementación concreta del TaskRepositoryPort usando SQLite.
"""

import sqlite3
import logging
from datetime import datetime, date, timedelta
from typing import List, Optional
from app.ports.outbound.task_repository import TaskRepositoryPort
from app.core.domain.task_models import (
    Task, Reminder, TaskStatistics, TaskStatus, TaskPriority
)

logger = logging.getLogger(__name__)


class SQLiteTaskRepository(TaskRepositoryPort):
    """
    Repositorio de tareas usando SQLite.
    
    Base de datos ligera con dos tablas:
    - tasks: Almacena las tareas
    - reminders: Almacena recordatorios
    """
    
    def __init__(self, db_path: str = "fisiagent.db"):
        """
        Inicializa el repositorio y crea las tablas si no existen.
        
        Args:
            db_path: Ruta a la base de datos SQLite
        """
        self.db_path = db_path
        self._init_database()
        logger.info(f"SQLiteTaskRepository inicializado: {db_path}")
    
    def _init_database(self):
        """Crea las tablas y índices si no existen."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Tabla de tareas
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                title TEXT NOT NULL,
                description TEXT NOT NULL DEFAULT '',
                due_date TEXT NOT NULL,
                priority INTEGER NOT NULL,
                status INTEGER NOT NULL DEFAULT 0,
                category TEXT NOT NULL DEFAULT 'general',
                estimated_hours REAL NOT NULL DEFAULT 1.0,
                completed_at TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Tabla de recordatorios
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS reminders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id INTEGER NOT NULL,
                remind_at TEXT NOT NULL,
                message TEXT NOT NULL DEFAULT '',
                is_sent INTEGER NOT NULL DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE
            )
        """)
        
        # Índices para performance
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_tasks_user_due 
            ON tasks(user_id, due_date)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_tasks_user_status 
            ON tasks(user_id, status)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_tasks_user_priority 
            ON tasks(user_id, priority)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_reminders_task 
            ON reminders(task_id)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_reminders_pending 
            ON reminders(remind_at, is_sent)
        """)
        
        conn.commit()
        conn.close()
        logger.info("Base de datos tasks/reminders inicializada")
    
    def save_task(self, task: Task) -> Task:
        """Guarda una nueva tarea."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO tasks (
                user_id, title, description, due_date, priority,
                status, category, estimated_hours, completed_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            task.user_id,
            task.title,
            task.description,
            task.due_date.isoformat(),
            task.priority.value,
            task.status.value,
            task.category,
            task.estimated_hours,
            task.completed_at.isoformat() if task.completed_at else None
        ))
        
        task_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        # Retornar tarea con ID asignado
        task.id = task_id
        task.created_at = datetime.now()
        
        logger.info(f"Tarea creada: ID={task_id}, user={task.user_id}")
        return task
    
    def get_task_by_id(self, task_id: int) -> Optional[Task]:
        """Recupera una tarea por ID."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, user_id, title, description, due_date, priority,
                   status, category, estimated_hours, completed_at, created_at
            FROM tasks
            WHERE id = ?
        """, (task_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return self._row_to_task(row)
        return None
    
    def get_user_tasks(
        self,
        user_id: str,
        status: Optional[TaskStatus] = None,
        priority: Optional[TaskPriority] = None,
        category: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[Task]:
        """Recupera tareas con filtros opcionales."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        query = """
            SELECT id, user_id, title, description, due_date, priority,
                   status, category, estimated_hours, completed_at, created_at
            FROM tasks
            WHERE user_id = ?
        """
        params = [user_id]
        
        if status is not None:
            query += " AND status = ?"
            params.append(status.value)
        
        if priority is not None:
            query += " AND priority = ?"
            params.append(priority.value)
        
        if category is not None:
            query += " AND category = ?"
            params.append(category)
        
        query += " ORDER BY due_date ASC, priority ASC"
        
        if limit is not None:
            query += " LIMIT ?"
            params.append(limit)
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        
        return [self._row_to_task(row) for row in rows]
    
    def get_upcoming_tasks(
        self,
        user_id: str,
        days_ahead: int = 7,
        limit: Optional[int] = None
    ) -> List[Task]:
        """Recupera tareas próximas por vencer."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        now = datetime.now()
        end_date = now + timedelta(days=days_ahead)
        
        query = """
            SELECT id, user_id, title, description, due_date, priority,
                   status, category, estimated_hours, completed_at, created_at
            FROM tasks
            WHERE user_id = ?
              AND status IN (0, 1)
              AND due_date BETWEEN ? AND ?
            ORDER BY due_date ASC, priority ASC
        """
        params = [user_id, now.isoformat(), end_date.isoformat()]
        
        if limit is not None:
            query += " LIMIT ?"
            params.append(limit)
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        
        tasks = [self._row_to_task(row) for row in rows]
        
        # Ordenar por urgency_score (calculado en el dominio)
        tasks.sort(key=lambda t: t.urgency_score, reverse=True)
        
        return tasks
    
    def get_overdue_tasks(self, user_id: str) -> List[Task]:
        """Recupera tareas vencidas."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        now = datetime.now()
        
        cursor.execute("""
            SELECT id, user_id, title, description, due_date, priority,
                   status, category, estimated_hours, completed_at, created_at
            FROM tasks
            WHERE user_id = ?
              AND status IN (0, 1)
              AND due_date < ?
            ORDER BY due_date ASC
        """, (user_id, now.isoformat()))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [self._row_to_task(row) for row in rows]
    
    def get_tasks_for_date(self, user_id: str, target_date: date) -> List[Task]:
        """Recupera tareas para una fecha específica."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        start = datetime.combine(target_date, datetime.min.time())
        end = datetime.combine(target_date, datetime.max.time())
        
        cursor.execute("""
            SELECT id, user_id, title, description, due_date, priority,
                   status, category, estimated_hours, completed_at, created_at
            FROM tasks
            WHERE user_id = ?
              AND due_date BETWEEN ? AND ?
            ORDER BY priority ASC, due_date ASC
        """, (user_id, start.isoformat(), end.isoformat()))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [self._row_to_task(row) for row in rows]
    
    def update_task(self, task: Task) -> Task:
        """Actualiza una tarea existente."""
        if task.id is None:
            raise ValueError("La tarea debe tener un ID para actualizarse")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE tasks
            SET title = ?,
                description = ?,
                due_date = ?,
                priority = ?,
                status = ?,
                category = ?,
                estimated_hours = ?,
                completed_at = ?
            WHERE id = ?
        """, (
            task.title,
            task.description,
            task.due_date.isoformat(),
            task.priority.value,
            task.status.value,
            task.category,
            task.estimated_hours,
            task.completed_at.isoformat() if task.completed_at else None,
            task.id
        ))
        
        conn.commit()
        affected = cursor.rowcount
        conn.close()
        
        if affected == 0:
            raise ValueError(f"Tarea con ID {task.id} no encontrada")
        
        logger.info(f"Tarea actualizada: ID={task.id}")
        return task
    
    def delete_task(self, task_id: int) -> bool:
        """Elimina una tarea."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        
        conn.commit()
        affected = cursor.rowcount
        conn.close()
        
        if affected > 0:
            logger.info(f"Tarea eliminada: ID={task_id}")
            return True
        return False
    
    def get_statistics(
        self,
        user_id: str,
        start_date: datetime,
        end_date: datetime
    ) -> TaskStatistics:
        """Calcula estadísticas de tareas."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Estadísticas generales
        cursor.execute("""
            SELECT
                COUNT(*) as total,
                SUM(CASE WHEN status = 2 THEN 1 ELSE 0 END) as completed,
                SUM(CASE WHEN status IN (0, 1) THEN 1 ELSE 0 END) as pending,
                SUM(CASE WHEN status IN (0, 1) AND due_date < ? THEN 1 ELSE 0 END) as overdue
            FROM tasks
            WHERE user_id = ?
              AND created_at BETWEEN ? AND ?
        """, (datetime.now().isoformat(), user_id, start_date.isoformat(), end_date.isoformat()))
        
        row = cursor.fetchone()
        total, completed, pending, overdue = row
        
        completion_rate = completed / total if total > 0 else 0.0
        
        # Tiempo promedio de completado
        cursor.execute("""
            SELECT AVG(
                CAST((julianday(completed_at) - julianday(created_at)) * 24 AS REAL)
            ) as avg_hours
            FROM tasks
            WHERE user_id = ?
              AND status = 2
              AND completed_at IS NOT NULL
              AND created_at BETWEEN ? AND ?
        """, (user_id, start_date.isoformat(), end_date.isoformat()))
        
        avg_hours_row = cursor.fetchone()
        avg_completion_time = avg_hours_row[0] if avg_hours_row[0] else 0.0
        
        # Distribución por prioridad
        cursor.execute("""
            SELECT priority, COUNT(*) as count
            FROM tasks
            WHERE user_id = ?
              AND created_at BETWEEN ? AND ?
            GROUP BY priority
        """, (user_id, start_date.isoformat(), end_date.isoformat()))
        
        priority_rows = cursor.fetchall()
        tasks_by_priority = {}
        for priority_val, count in priority_rows:
            priority = TaskPriority(priority_val)
            tasks_by_priority[priority.label] = count
        
        # Distribución por categoría
        cursor.execute("""
            SELECT category, COUNT(*) as count
            FROM tasks
            WHERE user_id = ?
              AND created_at BETWEEN ? AND ?
            GROUP BY category
        """, (user_id, start_date.isoformat(), end_date.isoformat()))
        
        category_rows = cursor.fetchall()
        tasks_by_category = {category: count for category, count in category_rows}
        
        conn.close()
        
        # Tendencia de productividad (simplificada)
        if completion_rate >= 0.7:
            trend = "mejorando"
        elif completion_rate >= 0.4:
            trend = "estable"
        else:
            trend = "decayendo"
        
        return TaskStatistics(
            user_id=user_id,
            period_start=start_date,
            period_end=end_date,
            total_tasks=total,
            completed_tasks=completed,
            pending_tasks=pending,
            overdue_tasks=overdue,
            completion_rate=completion_rate,
            avg_completion_time_hours=avg_completion_time,
            tasks_by_priority=tasks_by_priority,
            tasks_by_category=tasks_by_category,
            productivity_trend=trend
        )
    
    def save_reminder(self, reminder: Reminder) -> Reminder:
        """Guarda un recordatorio."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO reminders (task_id, remind_at, message, is_sent)
            VALUES (?, ?, ?, ?)
        """, (
            reminder.task_id,
            reminder.remind_at.isoformat(),
            reminder.message,
            1 if reminder.is_sent else 0
        ))
        
        reminder_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        reminder.id = reminder_id
        reminder.created_at = datetime.now()
        
        logger.info(f"Recordatorio creado: ID={reminder_id}, task={reminder.task_id}")
        return reminder
    
    def get_pending_reminders(self, before: datetime) -> List[Reminder]:
        """Recupera recordatorios pendientes."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, task_id, remind_at, message, is_sent, created_at
            FROM reminders
            WHERE is_sent = 0
              AND remind_at <= ?
            ORDER BY remind_at ASC
        """, (before.isoformat(),))
        
        rows = cursor.fetchall()
        conn.close()
        
        reminders = []
        for row in rows:
            reminders.append(Reminder(
                id=row[0],
                task_id=row[1],
                remind_at=datetime.fromisoformat(row[2]),
                message=row[3],
                is_sent=bool(row[4]),
                created_at=datetime.fromisoformat(row[5]) if row[5] else None
            ))
        
        return reminders
    
    def _row_to_task(self, row: tuple) -> Task:
        """Convierte una fila de SQLite a entidad Task."""
        return Task(
            id=row[0],
            user_id=row[1],
            title=row[2],
            description=row[3],
            due_date=datetime.fromisoformat(row[4]),
            priority=TaskPriority(row[5]),
            status=TaskStatus(row[6]),
            category=row[7],
            estimated_hours=row[8],
            completed_at=datetime.fromisoformat(row[9]) if row[9] else None,
            created_at=datetime.fromisoformat(row[10]) if row[10] else None
        )
