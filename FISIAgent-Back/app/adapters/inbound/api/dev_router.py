"""
DevRouter - Utilidad para sembrar datos de ejemplo en despliegues sin acceso a shell.

Pensado para plataformas como Render (free tier) donde no hay una terminal dentro
del contenedor para correr `seed_data.py` directo contra la base de datos. Este
endpoint hace lo mismo, vía HTTP, protegido por un token compartido.

Si no se configura la variable de entorno SEED_TOKEN, el endpoint queda deshabilitado.
"""
import logging
import os
import random
import sqlite3
from datetime import datetime, timedelta

from fastapi import APIRouter, Header, HTTPException

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/dev", tags=["Utilidades de desarrollo"])

DB_PATH = "fisiagent.db"
USER_ID = "estudiante_demo"


def _seed_mood_data(cursor, now: datetime) -> int:
    base_mood_pattern = [
        0, 0, 1, 1, 1, 2, 1, 0, 1, 1,
        2, 1, 1, 0, 0, 1, 1, 2, 2, 1,
        1, 0, 0, 1, 1, 0, 1, 1, 0, 0,
    ]
    notes_map = {
        0: ["¡Excelente día!", "Muy productivo", "Me siento genial", "Todo salió bien"],
        1: ["Día tranquilo", "Bien, sin novedades", "Normal", "Estable"],
        2: ["Un poco estresado", "Día difícil", "Preocupado por exámenes", "Cansado"],
        3: ["Muy estresado", "Me siento abrumado", "Día terrible", "Necesito ayuda"],
    }

    moods = []
    for i, mood_val in enumerate(base_mood_pattern):
        day = now - timedelta(days=29 - i)
        if random.random() < 0.2:
            mood_val = max(0, min(3, mood_val + random.choice([-1, 1])))
        moods.append((
            USER_ID,
            mood_val,
            random.choice(notes_map[mood_val]),
            day.strftime("%Y-%m-%d %H:%M:%S"),
            day.strftime("%Y-%m-%d %H:%M:%S"),
        ))

    cursor.executemany(
        """
        INSERT INTO mood_entries (user_id, mood, note, timestamp, created_at)
        VALUES (?, ?, ?, ?, ?)
        """,
        moods,
    )
    return len(moods)


def _seed_task_data(cursor, now: datetime) -> tuple[int, int]:
    tasks = [
        (USER_ID, "Entregar proyecto final de IA",
         "Completar la documentación y el código del proyecto de inteligencia artificial",
         (now + timedelta(days=2)).isoformat(), 0, 1, "académico", 8.0, None,
         (now - timedelta(days=10)).isoformat()),
        (USER_ID, "Estudiar para examen de Matemáticas",
         "Repasar los temas de cálculo diferencial e integral",
         (now + timedelta(days=5)).isoformat(), 1, 0, "académico", 6.0, None,
         (now - timedelta(days=7)).isoformat()),
        (USER_ID, "Leer capítulo 5 de Redes",
         "Leer y resumir el capítulo sobre protocolos de enrutamiento",
         (now - timedelta(days=3)).isoformat(), 2, 2, "académico", 3.0,
         (now - timedelta(days=4)).isoformat(), (now - timedelta(days=15)).isoformat()),
        (USER_ID, "Hacer laboratorio de Física",
         "Completar el reporte del laboratorio de circuitos eléctricos",
         (now - timedelta(days=1)).isoformat(), 1, 2, "académico", 4.0,
         (now - timedelta(days=2)).isoformat(), (now - timedelta(days=12)).isoformat()),
        (USER_ID, "Preparar presentación de Tesis",
         "Crear slides y practicar la exposición del avance de tesis",
         (now + timedelta(days=1)).isoformat(), 0, 0, "académico", 5.0, None,
         (now - timedelta(days=5)).isoformat()),
        (USER_ID, "Investigar para proyecto de Base de Datos",
         "Buscar información sobre bases de datos NoSQL",
         (now + timedelta(days=14)).isoformat(), 3, 0, "académico", 2.0, None,
         (now - timedelta(days=3)).isoformat()),
        (USER_ID, "Pagar recibo de luz",
         "Vence el plazo de pago, evitar corte de servicio",
         (now + timedelta(days=3)).isoformat(), 0, 0, "personal", 0.5, None,
         (now - timedelta(days=8)).isoformat()),
        (USER_ID, "Comprar víveres para la semana",
         "Ir al supermercado a comprar alimentos",
         (now - timedelta(days=2)).isoformat(), 2, 2, "personal", 1.5,
         (now - timedelta(days=3)).isoformat(), (now - timedelta(days=14)).isoformat()),
        (USER_ID, "Lavar el auto",
         "Llevar el auto al lavado o lavarlo en casa",
         (now - timedelta(days=5)).isoformat(), 3, 3, "personal", 1.0, None,
         (now - timedelta(days=20)).isoformat()),
        (USER_ID, "Renovar DNI",
         "Sacar cita en RENIEC para renovar el documento de identidad",
         (now + timedelta(days=7)).isoformat(), 1, 0, "personal", 2.0, None,
         (now - timedelta(days=6)).isoformat()),
        (USER_ID, "Ir al gimnasio",
         "Asistir a la rutina de ejercicios programada",
         (now - timedelta(days=1)).isoformat(), 2, 2, "bienestar", 1.0,
         (now - timedelta(days=1)).isoformat(), (now - timedelta(days=10)).isoformat()),
        (USER_ID, "Meditación diaria",
         "15 minutos de meditación guiada",
         now.isoformat(), 3, 2, "bienestar", 0.25,
         (now - timedelta(hours=2)).isoformat(), (now - timedelta(days=5)).isoformat()),
        (USER_ID, "Cita con el psicólogo",
         "Asistir a la consulta semanal de salud mental",
         (now + timedelta(days=4)).isoformat(), 1, 0, "bienestar", 1.0, None,
         (now - timedelta(days=9)).isoformat()),
        (USER_ID, "Caminata al aire libre",
         "Salir a caminar 30 minutos para despejar la mente",
         (now - timedelta(days=2)).isoformat(), 3, 2, "bienestar", 0.5,
         (now - timedelta(days=2)).isoformat(), (now - timedelta(days=18)).isoformat()),
        (USER_ID, "Leer correos pendientes",
         "Revisar y responder correos importantes",
         (now + timedelta(hours=6)).isoformat(), 2, 1, "general", 0.5, None,
         (now - timedelta(days=2)).isoformat()),
        (USER_ID, "Organizar escritorio",
         "Ordenar documentos y limpiar el área de trabajo",
         (now - timedelta(days=4)).isoformat(), 3, 2, "general", 1.0,
         (now - timedelta(days=5)).isoformat(), (now - timedelta(days=25)).isoformat()),
        (USER_ID, "Actualizar CV",
         "Agregar nuevas habilidades y experiencia al currículum",
         (now + timedelta(days=10)).isoformat(), 2, 0, "general", 2.0, None,
         (now - timedelta(days=4)).isoformat()),
    ]

    cursor.executemany(
        """
        INSERT INTO tasks (user_id, title, description, due_date, priority, status, category,
                          estimated_hours, completed_at, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        tasks,
    )

    cursor.execute("SELECT id, due_date FROM tasks WHERE user_id = ?", (USER_ID,))
    task_rows = cursor.fetchall()

    reminders = []
    for task_id, due_date in task_rows[:8]:
        remind_at = datetime.fromisoformat(due_date) - timedelta(hours=random.randint(2, 24))
        if remind_at > now:
            reminders.append((task_id, remind_at.isoformat(), "🔔 Recordatorio: tienes una tarea pendiente", 0))

    if reminders:
        cursor.executemany(
            """
            INSERT INTO reminders (task_id, remind_at, message, is_sent)
            VALUES (?, ?, ?, ?)
            """,
            reminders,
        )

    return len(tasks), len(reminders)


@router.post("/seed-demo-data")
def seed_demo_data(x_seed_token: str = Header(default="")):
    """
    Siembra datos de ejemplo (30 mood entries + 17 tareas) para `estudiante_demo`.

    Requiere el header `X-Seed-Token` igual a la variable de entorno SEED_TOKEN.
    Si SEED_TOKEN no está configurada, el endpoint responde 404 (deshabilitado).
    Es idempotente: borra los datos previos de `estudiante_demo` antes de sembrar.
    """
    expected_token = os.getenv("SEED_TOKEN", "")
    if not expected_token:
        raise HTTPException(status_code=404, detail="Not Found")
    if x_seed_token != expected_token:
        raise HTTPException(status_code=403, detail="Token inválido")

    now = datetime.now()
    conn = sqlite3.connect(DB_PATH)
    try:
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM reminders WHERE task_id IN (SELECT id FROM tasks WHERE user_id = ?)",
            (USER_ID,),
        )
        cursor.execute("DELETE FROM tasks WHERE user_id = ?", (USER_ID,))
        cursor.execute("DELETE FROM mood_entries WHERE user_id = ?", (USER_ID,))

        mood_count = _seed_mood_data(cursor, now)
        task_count, reminder_count = _seed_task_data(cursor, now)

        conn.commit()
    finally:
        conn.close()

    logger.info(f"[Seed] {mood_count} mood entries, {task_count} tareas, {reminder_count} recordatorios")

    return {
        "message": "Datos de ejemplo sembrados correctamente",
        "user_id": USER_ID,
        "mood_entries": mood_count,
        "tasks": task_count,
        "reminders": reminder_count,
    }
