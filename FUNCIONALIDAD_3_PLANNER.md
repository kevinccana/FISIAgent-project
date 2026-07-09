# Planificador Inteligente - Funcionalidad 3 Implementada ✅

## Resumen

Sistema completo de gestión de tareas con priorización inteligente mediante IA:
- **Persistencia:** SQLite (tabla `tasks` y `reminders` en `fisiagent.db`)
- **Arquitectura:** Hexagonal (Ports & Adapters)
- **IA:** Agente especializado (PlannerAgent) que usa Gemini para sugerencias
- **Endpoints:** CRUD completo + análisis de agenda + sugerencias de organización

---

## Arquitectura

### Estructura de componentes

```
app/
├── core/
│   ├── domain/
│   │   └── task_models.py                       # ✅ 7 entidades del dominio
│   │       ├── TaskPriority (enum)
│   │       ├── TaskStatus (enum)
│   │       ├── Task (con urgency_score calculado)
│   │       ├── Reminder
│   │       ├── TaskStatistics
│   │       ├── TaskSuggestion
│   │       └── DailySchedule
│   ├── agents/
│   │   └── planner_agent.py                     # ✅ Agente de IA
│   │       └── PlannerAgent (priorización inteligente)
│   └── use_cases/
│       └── task_use_cases.py                    # ✅ 10 casos de uso
│           ├── CreateTaskUseCase (con sugerencia opcional de IA)
│           ├── GetUpcomingTasksUseCase
│           ├── GetOverdueTasksUseCase
│           ├── UpdateTaskUseCase
│           ├── CompleteTaskUseCase
│           ├── DeleteTaskUseCase
│           ├── GetTaskStatisticsUseCase
│           ├── AnalyzeDailyScheduleUseCase (con IA)
│           ├── GetTaskOrganizationSuggestionsUseCase (con IA)
│           └── CreateReminderUseCase
│
├── ports/
│   └── outbound/
│       └── task_repository.py                   # ✅ Contrato de repositorio
│           └── TaskRepositoryPort (ABC)
│
├── adapters/
│   ├── outbound/
│   │   └── sqlite_task_repository.py            # ✅ Implementación SQLite
│   │       └── SQLiteTaskRepository
│   └── inbound/
│       └── api/
│           └── task_router.py                   # ✅ API REST (10 endpoints)
│               └── FastAPI router + DTOs
│
└── main.py                                      # ✅ Bootstrap + DI
```

---

## Base de Datos SQLite

### Tabla: `tasks`

```sql
CREATE TABLE tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    title TEXT NOT NULL,                      -- Máx 200 chars
    description TEXT NOT NULL DEFAULT '',     -- Máx 1000 chars
    due_date TEXT NOT NULL,                   -- ISO 8601 datetime
    priority INTEGER NOT NULL,                -- 0=URGENT, 1=HIGH, 2=MEDIUM, 3=LOW
    status INTEGER NOT NULL DEFAULT 0,        -- 0=PENDING, 1=IN_PROGRESS, 2=COMPLETED, 3=CANCELLED
    category TEXT NOT NULL DEFAULT 'general', -- académico, personal, bienestar, etc.
    estimated_hours REAL NOT NULL DEFAULT 1.0,
    completed_at TEXT,                        -- ISO 8601 datetime (nullable)
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- Índices para performance
CREATE INDEX idx_tasks_user_due ON tasks(user_id, due_date);
CREATE INDEX idx_tasks_user_status ON tasks(user_id, status);
CREATE INDEX idx_tasks_user_priority ON tasks(user_id, priority);
```

### Tabla: `reminders`

```sql
CREATE TABLE reminders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id INTEGER NOT NULL,
    remind_at TEXT NOT NULL,                  -- ISO 8601 datetime
    message TEXT NOT NULL DEFAULT '',
    is_sent INTEGER NOT NULL DEFAULT 0,       -- 0=pendiente, 1=enviado
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE
);

-- Índices
CREATE INDEX idx_reminders_task ON reminders(task_id);
CREATE INDEX idx_reminders_pending ON reminders(remind_at, is_sent);
```

**Ubicación:** `fisiagent.db` (auto-creado en la raíz del proyecto)

---

## API Endpoints

### 1. POST `/tasks/` - Crear tarea (con sugerencia de IA opcional)

**Request:**
```json
{
  "user_id": "estudiante_123",
  "title": "Entregar proyecto de BD2",
  "description": "Implementar stored procedures y triggers",
  "due_date": "2026-07-15T23:59:00",
  "priority": null,
  "category": "académico",
  "estimated_hours": 8.0,
  "auto_suggest_priority": true
}
```

**Response:** (201 Created)
```json
{
  "id": 1,
  "user_id": "estudiante_123",
  "title": "Entregar proyecto de BD2",
  "description": "Implementar stored procedures y triggers",
  "due_date": "2026-07-15T23:59:00",
  "priority": 1,
  "priority_label": "Alta",
  "priority_emoji": "🟠",
  "status": 0,
  "status_label": "Pendiente",
  "status_emoji": "⏳",
  "category": "académico",
  "estimated_hours": 8.0,
  "is_overdue": false,
  "days_until_due": 7,
  "urgency_score": 7.0,
  "completed_at": null,
  "created_at": "2026-07-08T10:00:00"
}
```

**Nota:** Si `auto_suggest_priority=true` y `priority=null`, el **PlannerAgent** usa IA para analizar:
- Contexto de tareas existentes del usuario
- Fecha límite
- Categoría y horas estimadas
- Carga de trabajo actual

**Y sugiere automáticamente la prioridad óptima.**

---

### 2. GET `/tasks/upcoming/{user_id}` - Tareas próximas a vencer

**Query Params:**
- `days` (default: 7) - Días hacia adelante
- `limit` (opcional) - Límite de resultados

**Example:** `/tasks/upcoming/estudiante_123?days=7&limit=10`

**Response:** (200 OK)
```json
[
  {
    "id": 3,
    "title": "Examen de Redes",
    "priority": 0,
    "priority_emoji": "🔴",
    "urgency_score": 9.5,
    "due_date": "2026-07-09T08:00:00",
    "days_until_due": 1,
    "is_overdue": false
  },
  {
    "id": 1,
    "title": "Entregar proyecto de BD2",
    "priority": 1,
    "priority_emoji": "🟠",
    "urgency_score": 7.0,
    "due_date": "2026-07-15T23:59:00",
    "days_until_due": 7,
    "is_overdue": false
  }
]
```

**Nota:** Las tareas se ordenan automáticamente por `urgency_score` (calculado con algoritmo del dominio).

---

### 3. GET `/tasks/overdue/{user_id}` - Tareas vencidas

**Response:** (200 OK)
```json
[
  {
    "id": 5,
    "title": "Leer artículo de IA",
    "priority": 2,
    "due_date": "2026-07-05T23:59:00",
    "days_until_due": -3,
    "is_overdue": true
  }
]
```

---

### 4. GET `/tasks/statistics/{user_id}` - Estadísticas de productividad

**Query Params:**
- `days` (default: 30) - Período de análisis

**Response:** (200 OK)
```json
{
  "user_id": "estudiante_123",
  "period_start": "2026-06-08T00:00:00",
  "period_end": "2026-07-08T23:59:59",
  "total_tasks": 35,
  "completed_tasks": 28,
  "pending_tasks": 5,
  "overdue_tasks": 2,
  "completion_rate": 0.8,
  "completion_percentage": 80.0,
  "avg_completion_time_hours": 18.5,
  "tasks_by_priority": {
    "Urgente": 3,
    "Alta": 15,
    "Media": 12,
    "Baja": 5
  },
  "tasks_by_category": {
    "académico": 25,
    "personal": 8,
    "bienestar": 2
  },
  "productivity_trend": "mejorando"
}
```

**Tendencias:**
- `"mejorando"`: completion_rate >= 70%
- `"estable"`: completion_rate >= 40%
- `"decayendo"`: completion_rate < 40%

---

### 5. GET `/tasks/schedule/{user_id}/{target_date}` - Análisis de agenda diaria con IA ⭐

**Example:** `/tasks/schedule/estudiante_123/2026-07-10`

**Response:** (200 OK)
```json
{
  "date": "2026-07-10",
  "tasks": [
    {
      "id": 7,
      "title": "Estudiar para examen de Redes",
      "estimated_hours": 4.0,
      "priority": 0,
      "priority_emoji": "🔴"
    },
    {
      "id": 8,
      "title": "Hacer ejercicios de Algoritmos",
      "estimated_hours": 2.5,
      "priority": 1,
      "priority_emoji": "🟠"
    },
    {
      "id": 9,
      "title": "Leer paper de ML",
      "estimated_hours": 1.5,
      "priority": 2,
      "priority_emoji": "🟡"
    }
  ],
  "total_estimated_hours": 8.0,
  "is_feasible": true,
  "is_overloaded": false,
  "recommendations": [
    "Tu carga del día es manejable (8.0 horas estimadas).",
    "Prioriza el estudio para Redes en las primeras horas del día cuando estás más concentrado.",
    "Después de 4 horas de estudio, toma un descanso de 15-20 minutos antes de continuar.",
    "Considera hacer ejercicio o salir a caminar entre el estudio de Redes y los ejercicios de Algoritmos.",
    "Si terminas temprano, dedica tiempo a relajarte - no todo debe ser académico."
  ]
}
```

**Funcionamiento:**
El **PlannerAgent** analiza la carga del día y genera recomendaciones personalizadas considerando:
- Total de horas estimadas
- Distribución de prioridades
- Tareas vencidas
- Balance entre trabajo y descanso

---

### 6. GET `/tasks/suggestions/{user_id}` - Sugerencias de organización general con IA ⭐

**Response:** (200 OK)
```json
{
  "diagnosis": "Tienes una buena gestión de tareas en general, pero hay 2 tareas vencidas que requieren atención inmediata. Tu tasa de completitud es alta (80%), lo que indica disciplina.",
  "recommendations": [
    "Prioriza inmediatamente las 2 tareas vencidas. Si alguna ya no es relevante, cancélala en lugar de dejarla pendiente.",
    "Tu tendencia de productividad es 'mejorando', sigue así. Considera establecer un ritual diario para revisar tus tareas cada mañana.",
    "Tienes 5 tareas pendientes con prioridad 'Urgente' o 'Alta'. Bloquea tiempo en tu calendario específicamente para ellas.",
    "Divide las tareas grandes (>5 horas estimadas) en subtareas más pequeñas para reducir la procrastinación.",
    "No olvides incluir tiempo para bienestar personal. Solo tienes 2 tareas de esa categoría - considera agregar actividades de autocuidado."
  ],
  "critical_tasks_count": 2,
  "overdue_count": 2
}
```

**Funcionamiento:**
El **PlannerAgent** analiza todas las tareas del usuario y proporciona:
- **Diagnóstico:** Evaluación general de la gestión de tareas
- **Recomendaciones:** 3-5 consejos específicos y accionables
- **Alertas:** Detección de tareas críticas/vencidas

---

### 7. PUT `/tasks/{task_id}` - Actualizar tarea

**Request:**
```json
{
  "title": "Entregar proyecto de BD2 (versión final)",
  "priority": 0,
  "status": 1
}
```

**Response:** (200 OK)
```json
{
  "id": 1,
  "title": "Entregar proyecto de BD2 (versión final)",
  "priority": 0,
  "priority_label": "Urgente",
  "status": 1,
  "status_label": "En progreso",
  ...
}
```

---

### 8. POST `/tasks/{task_id}/complete` - Marcar como completada

**Response:** (200 OK)
```json
{
  "id": 1,
  "status": 2,
  "status_label": "Completada",
  "status_emoji": "✅",
  "completed_at": "2026-07-08T15:30:00",
  ...
}
```

---

### 9. DELETE `/tasks/{task_id}` - Eliminar tarea

**Response:** (200 OK)
```json
{
  "message": "Tarea eliminada correctamente",
  "id": 1
}
```

---

### 10. POST `/tasks/reminders` - Crear recordatorio

**Request:**
```json
{
  "task_id": 1,
  "remind_at": "2026-07-14T08:00:00",
  "message": "Recuerda: entregar proyecto de BD2 mañana"
}
```

**Response:** (201 Created)
```json
{
  "id": 1,
  "task_id": 1,
  "remind_at": "2026-07-14T08:00:00",
  "message": "Recuerda: entregar proyecto de BD2 mañana",
  "is_sent": false,
  "created_at": "2026-07-08T10:00:00"
}
```

---

## PlannerAgent - Inteligencia Artificial

### Capacidades del agente

#### 1. Sugerencia de prioridad (`suggest_priority`)

**Entrada:**
- Nueva tarea a crear
- Tareas existentes del usuario (contexto)

**Proceso:**
```python
SYSTEM_INSTRUCTION = """
Eres un asistente de planificación para estudiantes.
Analiza la nueva tarea considerando:
- Fecha límite (urgencia temporal)
- Contexto de tareas existentes
- Carga de trabajo actual
- Categoría (académico, personal, etc.)

Sugiere prioridad: URGENT (0), HIGH (1), MEDIUM (2), o LOW (3)
"""
```

**Salida:**
- Prioridad sugerida (0-3)
- Razonamiento (2-3 oraciones)
- 2-3 consejos prácticos

**Ejemplo:**
```
PRIORIDAD: 1
RAZONAMIENTO: El proyecto de BD2 vence en 7 días y requiere 8 horas. 
Considerando tu carga actual de 5 tareas pendientes, es importante 
comenzar pronto pero no es urgente inmediato.
CONSEJO_1: Divide el proyecto en tareas de 2 horas cada una
CONSEJO_2: Trabaja en las stored procedures primero, son la base
CONSEJO_3: Dedica las mañanas a este proyecto cuando estás más concentrado
```

#### 2. Análisis de agenda (`analyze_schedule`)

**Entrada:**
- Fecha objetivo
- Tareas programadas para ese día

**Proceso:**
- Calcula horas totales
- Detecta sobrecarga (>8 horas)
- Identifica tareas vencidas
- Analiza distribución de prioridades

**Salida:**
- `is_feasible`: true/false
- `is_overloaded`: true si >8 horas
- Recomendaciones:
  - Si sobrecarga: sugiere qué tareas posponer
  - Si holgado: sugiere tiempo para descanso/estudio adicional
  - Si urgentes: sugiere orden de ejecución

#### 3. Sugerencias de organización (`suggest_organization`)

**Entrada:**
- Todas las tareas del usuario
- Contexto general (total, pendientes, vencidas)

**Proceso:**
- Diagnóstica gestión general de tareas
- Identifica patrones problemáticos
- Detecta desequilibrios (ej: muchas académicas, pocas de bienestar)

**Salida:**
- Diagnóstico: evaluación en lenguaje natural
- 3-5 recomendaciones específicas
- Alertas si hay situación crítica

---

## Algoritmo de Urgency Score

Cada tarea tiene un `urgency_score` calculado automáticamente (rango: 0.0 a 10.0):

```python
def urgency_score(self) -> float:
    # Factor de prioridad (0.0 a 4.0)
    priority_weight = {
        URGENT: 4.0,
        HIGH: 3.0,
        MEDIUM: 2.0,
        LOW: 1.0
    }
    priority_score = priority_weight[self.priority]
    
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
```

**Ejemplos:**
- Tarea URGENT vencida: 4.0 + 6.0 = **10.0** (máxima urgencia)
- Tarea HIGH para mañana: 3.0 + 5.0 = **8.0**
- Tarea MEDIUM en 1 semana: 2.0 + 3.0 = **5.0**
- Tarea LOW en 1 mes: 1.0 + 1.0 = **2.0**

---

## Testing

### Crear tareas de prueba

```bash
# 1. Tarea urgente (examen mañana)
curl -X POST http://localhost:8000/tasks/ \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test_user",
    "title": "Examen de Redes",
    "description": "Temas 1-5",
    "due_date": "2026-07-09T08:00:00",
    "priority": 0,
    "category": "académico",
    "estimated_hours": 6.0
  }'

# 2. Tarea con sugerencia de IA
curl -X POST http://localhost:8000/tasks/ \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test_user",
    "title": "Proyecto de IA",
    "description": "Implementar red neuronal",
    "due_date": "2026-07-20T23:59:00",
    "priority": null,
    "category": "académico",
    "estimated_hours": 15.0,
    "auto_suggest_priority": true
  }'

# 3. Tarea personal
curl -X POST http://localhost:8000/tasks/ \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test_user",
    "title": "Ir al gimnasio",
    "description": "Rutina de piernas",
    "due_date": "2026-07-10T18:00:00",
    "priority": 3,
    "category": "bienestar",
    "estimated_hours": 1.5
  }'
```

### Consultar tareas próximas

```bash
curl http://localhost:8000/tasks/upcoming/test_user?days=7&limit=10
```

### Analizar agenda con IA

```bash
curl http://localhost:8000/tasks/schedule/test_user/2026-07-10
```

### Obtener sugerencias de organización

```bash
curl http://localhost:8000/tasks/suggestions/test_user
```

### Completar tarea

```bash
curl -X POST http://localhost:8000/tasks/1/complete
```

### Ver estadísticas

```bash
curl http://localhost:8000/tasks/statistics/test_user?days=30
```

---

## Integración con Frontend

Actualizar `src/services/api.js`:

```javascript
// Crear tarea con sugerencia de IA
export const createTask = async (userId, taskData, autoSuggest = false) => {
  const response = await axios.post('/tasks/', {
    user_id: userId,
    ...taskData,
    auto_suggest_priority: autoSuggest
  });
  return response.data;
};

// Obtener tareas próximas
export const getUpcomingTasks = async (userId, days = 7) => {
  const response = await axios.get(`/tasks/upcoming/${userId}`, {
    params: { days }
  });
  return response.data;
};

// Analizar agenda diaria
export const analyzeDailySchedule = async (userId, date) => {
  const response = await axios.get(`/tasks/schedule/${userId}/${date}`);
  return response.data;
};

// Obtener sugerencias de organización
export const getOrganizationSuggestions = async (userId) => {
  const response = await axios.get(`/tasks/suggestions/${userId}`);
  return response.data;
};

// Completar tarea
export const completeTask = async (taskId) => {
  const response = await axios.post(`/tasks/${taskId}/complete`);
  return response.data;
};

// Obtener estadísticas
export const getTaskStatistics = async (userId, days = 30) => {
  const response = await axios.get(`/tasks/statistics/${userId}`, {
    params: { days }
  });
  return response.data;
};
```

---

## Arquitectura Hexagonal Aplicada

**Flujo de una petición con IA:**

```
HTTP POST /tasks/ (auto_suggest_priority=true)
    ↓
task_router.py (Adapter Inbound)
    ↓
CreateTaskUseCase (Core)
    ↓ (si auto_suggest_priority)
    ┌─────────────────────────┐
    │ PlannerAgent (AI)       │
    │ - Analiza contexto      │
    │ - Usa Gemini para       │
    │   sugerir prioridad     │
    └─────────────────────────┘
    ↓
TaskRepositoryPort (Interface)
    ↓
SQLiteTaskRepository (Adapter Outbound)
    ↓
SQLite DB (fisiagent.db)
```

**Beneficios:**
- ✅ IA encapsulada en agente especializado
- ✅ Repositorio intercambiable (SQLite → PostgreSQL → MongoDB)
- ✅ Casos de uso testables sin dependencias externas
- ✅ Agente reutilizable en múltiples casos de uso

---

## Estado de la Funcionalidad 3

| Componente | Estado |
|------------|--------|
| **Modelos de dominio (7)** | ✅ Completo |
| **Port de repositorio** | ✅ Completo |
| **Adapter SQLite** | ✅ Completo (2 tablas) |
| **PlannerAgent con IA** | ✅ Completo (3 acciones) |
| **Casos de uso (10)** | ✅ Completo |
| **API Router (10 endpoints)** | ✅ Completo |
| **Bootstrap en main.py** | ✅ Completo |
| **Urgency score algorithm** | ✅ Implementado |
| **Documentación** | ✅ Completo |
| **Integración frontend** | ⏳ Pendiente |

---

## Logs de Startup

Al iniciar el servidor:

```
[Startup] Inicializando Planificador Inteligente...
[Startup] SQLiteTaskRepository inicializado: fisiagent.db
[Startup] Base de datos tasks/reminders inicializada
[Startup] ✓ PlannerAgent inicializado
[Startup] ✓ Planificador Inteligente inicializado (SQLite + IA)
[Startup] 🚀 FISIAgent listo
[Startup] 📊 Funcionalidades:
[Startup]    ✅ Funcionalidad 1: Chat de Apoyo Emocional (RAG + Agentes)
[Startup]    ✅ Funcionalidad 2: Dashboard de Bienestar (SQLite)
[Startup]    ✅ Funcionalidad 3: Planificador Inteligente (Tasks + IA)
```

---

## Próximas Mejoras (Opcionales)

### 1. Integración con Google Calendar
- Sincronizar tareas con eventos del calendario
- Importar/exportar tareas

### 2. Notificaciones Push
- Enviar recordatorios por correo/SMS
- Alertas de tareas vencidas

### 3. Análisis predictivo
- Predecir probabilidad de completar tarea a tiempo
- Sugerir redistribución de carga semanal

### 4. Subtareas
- Dividir tareas grandes en subtareas
- Tracking de progreso por subtarea

### 5. Gamificación
- Puntos por tareas completadas
- Rachas de productividad
- Logros y badges

### 6. Colaboración
- Asignar tareas a otros estudiantes
- Tareas grupales

---

## Resumen Final

✅ **Funcionalidad 3 implementada completamente:**
- 7 modelos de dominio con validaciones
- 1 agente de IA (PlannerAgent) con 3 capacidades
- 10 casos de uso cubriendo todo el ciclo de vida
- 2 tablas SQLite con índices optimizados
- 10 endpoints REST con DTOs
- Priorización inteligente con Gemini
- Análisis de agenda y sugerencias personalizadas
- Algoritmo de urgency_score
- Documentación completa

🎯 **Proyecto cumple requisito: 3 funcionalidades end-to-end implementadas.**
