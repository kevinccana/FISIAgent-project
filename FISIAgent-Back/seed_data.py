"""
Script para insertar datos de ejemplo en fisiagent.db
para las funcionalidades:
  - Funcionalidad 2: Dashboard de estado de ánimo (mood_entries)
  - Funcionalidad 3: Planificador de tareas (tasks, reminders)
"""

import sqlite3
import os
from datetime import datetime, timedelta
import random

DB_PATH = os.path.join(os.path.dirname(__file__), "fisiagent.db")
USER_ID = "estudiante_demo"
NOW = datetime.now()

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def clear_existing_data(conn):
    """Limpia datos existentes del usuario demo para evitar duplicados."""
    cursor = conn.cursor()
    cursor.execute("DELETE FROM reminders WHERE task_id IN (SELECT id FROM tasks WHERE user_id = ?)", (USER_ID,))
    cursor.execute("DELETE FROM tasks WHERE user_id = ?", (USER_ID,))
    cursor.execute("DELETE FROM mood_entries WHERE user_id = ?", (USER_ID,))
    conn.commit()
    print("✅ Datos existentes limpiados.")

# ============================================================
# FUNCIONALIDAD 2: DATOS DE ESTADO DE ÁNIMO (MOOD)
# ============================================================
def seed_mood_data(conn):
    """
    Inserta 30 registros de estado de ánimo para el último mes.
    Escala: 0=Muy bien 😊, 1=Bien 🙂, 2=Mal 😟, 3=Muy mal 😢
    """
    cursor = conn.cursor()
    moods = []
    
    # Crear patrón realista: mayoría bien, algunos altibajos
    base_mood_pattern = [0, 0, 1, 1, 1, 2, 1, 0, 1, 1,  # días 1-10
                         2, 1, 1, 0, 0, 1, 1, 2, 2, 1,  # días 11-20
                         1, 0, 0, 1, 1, 0, 1, 1, 0, 0]   # días 21-30
    
    for i, mood_val in enumerate(base_mood_pattern):
        day = NOW - timedelta(days=29 - i)
        # Añadir algo de variación aleatoria
        if random.random() < 0.2:
            mood_val = max(0, min(3, mood_val + random.choice([-1, 1])))
        
        notes_map = {
            0: random.choice(["¡Excelente día!", "Muy productivo", "Me siento genial", "Todo salió bien"]),
            1: random.choice(["Día tranquilo", "Bien, sin novedades", "Normal", "Estable"]),
            2: random.choice(["Un poco estresado", "Día difícil", "Preocupado por exámenes", "Cansado"]),
            3: random.choice(["Muy estresado", "Me siento abrumado", "Día terrible", "Necesito ayuda"]),
        }
        
        moods.append((
            USER_ID,
            mood_val,
            notes_map[mood_val],
            day.strftime("%Y-%m-%d %H:%M:%S"),
            day.strftime("%Y-%m-%d %H:%M:%S")
        ))
    
    cursor.executemany("""
        INSERT INTO mood_entries (user_id, mood, note, timestamp, created_at)
        VALUES (?, ?, ?, ?, ?)
    """, moods)
    conn.commit()
    print(f"✅ {len(moods)} registros de estado de ánimo insertados.")

# ============================================================
# FUNCIONALIDAD 3: DATOS DE TAREAS (TASKS)
# ============================================================
def seed_task_data(conn):
    """
    Inserta tareas de ejemplo con diferentes estados, prioridades y categorías.
    TaskStatus: 0=PENDING, 1=IN_PROGRESS, 2=COMPLETED, 3=CANCELLED
    TaskPriority: 0=URGENT🔴, 1=HIGH🟠, 2=MEDIUM🟡, 3=LOW🟢
    Categorías: académico, personal, bienestar, general
    """
    cursor = conn.cursor()
    
    tasks = [
        # (user_id, title, description, due_date, priority, status, category, estimated_hours, completed_at, created_at)
        
        # === TAREAS ACADÉMICAS ===
        (USER_ID, "Entregar proyecto final de IA", 
         "Completar la documentación y el código del proyecto de inteligencia artificial", 
         (NOW + timedelta(days=2)).isoformat(),
         0, 1, "académico", 8.0, 
         None,
         (NOW - timedelta(days=10)).isoformat()),
        
        (USER_ID, "Estudiar para examen de Matemáticas", 
         "Repasar los temas de cálculo diferencial e integral", 
         (NOW + timedelta(days=5)).isoformat(),
         1, 0, "académico", 6.0, 
         None,
         (NOW - timedelta(days=7)).isoformat()),
        
        (USER_ID, "Leer capítulo 5 de Redes", 
         "Leer y resumir el capítulo sobre protocolos de enrutamiento", 
         (NOW - timedelta(days=3)).isoformat(),
         2, 2, "académico", 3.0, 
         (NOW - timedelta(days=4)).isoformat(),
         (NOW - timedelta(days=15)).isoformat()),
        
        (USER_ID, "Hacer laboratorio de Física", 
         "Completar el reporte del laboratorio de circuitos eléctricos", 
         (NOW - timedelta(days=1)).isoformat(),
         1, 2, "académico", 4.0, 
         (NOW - timedelta(days=2)).isoformat(),
         (NOW - timedelta(days=12)).isoformat()),
        
        (USER_ID, "Preparar presentación de Tesis", 
         "Crear slides y practicar la exposición del avance de tesis", 
         (NOW + timedelta(days=1)).isoformat(),
         0, 0, "académico", 5.0, 
         None,
         (NOW - timedelta(days=5)).isoformat()),
        
        (USER_ID, "Investigar para proyecto de Base de Datos", 
         "Buscar información sobre bases de datos NoSQL", 
         (NOW + timedelta(days=14)).isoformat(),
         3, 0, "académico", 2.0, 
         None,
         (NOW - timedelta(days=3)).isoformat()),
        
        # === TAREAS PERSONALES ===
        (USER_ID, "Pagar recibo de luz", 
         "Vence el plazo de pago, evitar corte de servicio", 
         (NOW + timedelta(days=3)).isoformat(),
         0, 0, "personal", 0.5, 
         None,
         (NOW - timedelta(days=8)).isoformat()),
        
        (USER_ID, "Comprar víveres para la semana", 
         "Ir al supermercado a comprar alimentos", 
         (NOW - timedelta(days=2)).isoformat(),
         2, 2, "personal", 1.5, 
         (NOW - timedelta(days=3)).isoformat(),
         (NOW - timedelta(days=14)).isoformat()),
        
        (USER_ID, "Lavar el auto", 
         "Llevar el auto al lavado o lavarlo en casa", 
         (NOW - timedelta(days=5)).isoformat(),
         3, 3, "personal", 1.0, 
         None,
         (NOW - timedelta(days=20)).isoformat()),
        
        (USER_ID, "Renovar DNI", 
         "Sacar cita en RENIEC para renovar el documento de identidad", 
         (NOW + timedelta(days=7)).isoformat(),
         1, 0, "personal", 2.0, 
         None,
         (NOW - timedelta(days=6)).isoformat()),
        
        # === TAREAS DE BIENESTAR ===
        (USER_ID, "Ir al gimnasio", 
         "Asistir a la rutina de ejercicios programada", 
         (NOW - timedelta(days=1)).isoformat(),
         2, 2, "bienestar", 1.0, 
         (NOW - timedelta(days=1)).isoformat(),
         (NOW - timedelta(days=10)).isoformat()),
        
        (USER_ID, "Meditación diaria", 
         "15 minutos de meditación guiada", 
         (NOW - timedelta(days=0)).isoformat(),
         3, 2, "bienestar", 0.25, 
         (NOW - timedelta(hours=2)).isoformat(),
         (NOW - timedelta(days=5)).isoformat()),
        
        (USER_ID, "Cita con el psicólogo", 
         "Asistir a la consulta semanal de salud mental", 
         (NOW + timedelta(days=4)).isoformat(),
         1, 0, "bienestar", 1.0, 
         None,
         (NOW - timedelta(days=9)).isoformat()),
        
        (USER_ID, "Caminata al aire libre", 
         "Salir a caminar 30 minutos para despejar la mente", 
         (NOW - timedelta(days=2)).isoformat(),
         3, 2, "bienestar", 0.5, 
         (NOW - timedelta(days=2)).isoformat(),
         (NOW - timedelta(days=18)).isoformat()),
        
        # === TAREAS GENERALES ===
        (USER_ID, "Leer correos pendientes", 
         "Revisar y responder correos importantes", 
         (NOW + timedelta(hours=6)).isoformat(),
         2, 1, "general", 0.5, 
         None,
         (NOW - timedelta(days=2)).isoformat()),
        
        (USER_ID, "Organizar escritorio", 
         "Ordenar documentos y limpiar el área de trabajo", 
         (NOW - timedelta(days=4)).isoformat(),
         3, 2, "general", 1.0, 
         (NOW - timedelta(days=5)).isoformat(),
         (NOW - timedelta(days=25)).isoformat()),
        
        (USER_ID, "Actualizar CV", 
         "Agregar nuevas habilidades y experiencia al currículum", 
         (NOW + timedelta(days=10)).isoformat(),
         2, 0, "general", 2.0, 
         None,
         (NOW - timedelta(days=4)).isoformat()),
    ]
    
    cursor.executemany("""
        INSERT INTO tasks (user_id, title, description, due_date, priority, status, category, 
                          estimated_hours, completed_at, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, tasks)
    conn.commit()
    print(f"✅ {len(tasks)} tareas insertadas.")
    
    # Obtener IDs de tareas insertadas para crear recordatorios
    cursor.execute("SELECT id, due_date FROM tasks WHERE user_id = ?", (USER_ID,))
    task_ids = cursor.fetchall()
    
    # Crear recordatorios para algunas tareas
    reminders = []
    for task in task_ids[:8]:  # Primeras 8 tareas tienen recordatorio
        remind_at = datetime.fromisoformat(task["due_date"]) - timedelta(hours=random.randint(2, 24))
        if remind_at > NOW:
            reminders.append((
                task["id"],
                remind_at.isoformat(),
                f"🔔 Recordatorio: tienes una tarea pendiente",
                0  # is_sent = False
            ))
    
    if reminders:
        cursor.executemany("""
            INSERT INTO reminders (task_id, remind_at, message, is_sent)
            VALUES (?, ?, ?, ?)
        """, reminders)
        conn.commit()
        print(f"✅ {len(reminders)} recordatorios creados.")
    
    return task_ids

def main():
    print("=" * 60)
    print("  🌱 SEMILLA DE DATOS DE EJEMPLO - FISIAgent")
    print("=" * 60)
    print(f"  Usuario: {USER_ID}")
    print(f"  Base de datos: {DB_PATH}")
    print(f"  Fecha actual: {NOW.strftime('%Y-%m-%d %H:%M')}")
    print("=" * 60)
    print()
    
    conn = get_conn()
    clear_existing_data(conn)
    
    print("\n📊 FUNCIONALIDAD 2 - Dashboard de Estado de Ánimo")
    print("-" * 50)
    seed_mood_data(conn)
    
    print("\n📋 FUNCIONALIDAD 3 - Planificador de Tareas")
    print("-" * 50)
    seed_task_data(conn)
    
    conn.close()
    
    print("\n" + "=" * 60)
    print("  ✅ ¡Datos de ejemplo insertados correctamente!")
    print("=" * 60)
    print()
    print("  📊 Mood: 30 registros de estado de ánimo (últimos 30 días)")
    print("  📋 Tasks: 17 tareas con varios estados/prioridades/categorías")
    print("  🔔 Reminders: Recordatorios para tareas futuras")
    print()
    print("  🚀 Reinicia el backend para ver los cambios:")
    print("     Presiona Ctrl+C en la terminal de uvicorn y vuelve a iniciarlo")
    print()

if __name__ == "__main__":
    main()