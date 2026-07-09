# Dashboard de Bienestar - Funcionalidad 2 Implementada ✅

## Resumen

Sistema completo de registro y análisis de estados de ánimo implementado con:
- **Persistencia:** SQLite (base de datos ligera en `fisiagent.db`)
- **Arquitectura:** Hexagonal (Ports & Adapters)
- **Endpoints:** CRUD completo + insights automáticos

---

## Arquitectura

### Estructura de componentes

```
app/
├── core/
│   ├── domain/
│   │   └── mood_models.py                      # ✅ Entidades del dominio
│   │       ├── MoodLevel (enum)
│   │       ├── MoodEntry
│   │       ├── MoodStatistics
│   │       ├── MonthlyMoodSummary
│   │       └── DailyMoodEntry
│   └── use_cases/
│       └── mood_use_cases.py                   # ✅ Lógica de negocio
│           ├── RegisterMoodUseCase
│           ├── GetMoodHistoryUseCase
│           ├── GetMonthlyCalendarUseCase
│           ├── GetMoodInsightsUseCase
│           ├── UpdateMoodUseCase
│           └── DeleteMoodUseCase
│
├── ports/
│   └── outbound/
│       └── mood_repository.py                  # ✅ Contrato de repositorio
│           └── MoodLogRepositoryPort (ABC)
│
├── adapters/
│   ├── outbound/
│   │   └── sqlite_mood_repository.py           # ✅ Implementación SQLite
│   │       └── SQLiteMoodLogRepository
│   └── inbound/
│       └── api/
│           └── mood_router.py                  # ✅ API REST
│               └── FastAPI router + DTOs
│
└── main.py                                     # ✅ Bootstrap + DI
```

---

## Base de Datos SQLite

### Tabla: `mood_entries`

```sql
CREATE TABLE mood_entries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,                    -- ID del usuario (futuro: auth)
    mood INTEGER NOT NULL,                    -- 0=Muy bien, 1=Bien, 2=Mal, 3=Muy mal
    note TEXT NOT NULL DEFAULT '',            -- Nota opcional (máx 500 chars)
    timestamp TEXT NOT NULL,                  -- ISO 8601 datetime
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- Índices para performance
CREATE INDEX idx_user_timestamp ON mood_entries(user_id, timestamp DESC);
CREATE INDEX idx_user_month ON mood_entries(user_id, strftime('%Y-%m', timestamp));
```

**Ubicación:** `fisiagent.db` (auto-creado en la raíz del proyecto)

---

## API Endpoints

### 1. POST `/mood/register` - Registrar estado de ánimo

**Request:**
```json
{
  "user_id": "estudiante_123",
  "mood": 1,
  "note": "Día tranquilo y productivo"
}
```

**Response:** (201 Created)
```json
{
  "id": 1,
  "user_id": "estudiante_123",
  "mood": 1,
  "mood_label": "Bien",
  "note": "Día tranquilo y productivo",
  "timestamp": "2026-07-08T14:30:00"
}
```

---

### 2. GET `/mood/history/{user_id}` - Historial de registros

**Query Params:**
- `days` (default: 30) - Número de días hacia atrás
- `limit` (opcional) - Límite de resultados

**Response:** (200 OK)
```json
[
  {
    "id": 5,
    "user_id": "estudiante_123",
    "mood": 0,
    "mood_label": "Muy bien",
    "note": "Excelente día con amigos",
    "timestamp": "2026-07-08T10:00:00"
  },
  {
    "id": 4,
    "user_id": "estudiante_123",
    "mood": 2,
    "mood_label": "Mal",
    "note": "Estrés por exámenes",
    "timestamp": "2026-07-07T18:30:00"
  }
]
```

---

### 3. GET `/mood/calendar/{user_id}/{year}/{month}` - Calendario mensual

**Example:** `/mood/calendar/estudiante_123/2026/7`

**Response:** (200 OK)
```json
{
  "year": 2026,
  "month": 7,
  "entries": {
    "1": {"mood": 0, "note": "Gran día"},
    "3": {"mood": 1, "note": ""},
    "5": {"mood": 2, "note": "Estresante"},
    "8": {"mood": 0, "note": "Salida con amigos"}
  }
}
```

**Uso:** El frontend usa esto para renderizar el calendario con colores según el mood.

---

### 4. GET `/mood/insights/{user_id}` - Insights y recomendaciones

**Query Params:**
- `days` (default: 30) - Período de análisis

**Response:** (200 OK)
```json
{
  "statistics": {
    "period_start": "2026-06-08T00:00:00",
    "period_end": "2026-07-08T23:59:59",
    "total_entries": 25,
    "avg_mood": 1.2,
    "mood_distribution": {
      "Muy bien": 8,
      "Bien": 12,
      "Mal": 4,
      "Muy mal": 1
    },
    "most_common_mood": "Bien",
    "mood_trend": "positivo"
  },
  "monthly_history": [
    {"year": 2026, "month": 5, "month_label": "May", "avg_mood": 1.5, "entry_count": 18},
    {"year": 2026, "month": 6, "month_label": "Jun", "avg_mood": 1.3, "entry_count": 22},
    {"year": 2026, "month": 7, "month_label": "Jul", "avg_mood": 1.2, "entry_count": 25}
  ],
  "insights": [
    "🎉 Tu estado de ánimo ha sido mayormente positivo (promedio: 1.2/3.0)",
    "Tu estado más frecuente es 'Bien' (48% del tiempo)",
    "Tuviste 1 días especialmente difíciles. Recuerda que está bien pedir ayuda.",
    "📈 Tu ánimo ha mejorado respecto al mes anterior (+0.1 puntos)"
  ],
  "recommendations": [
    "Sigue registrando tu ánimo para que podamos darte mejores recomendaciones.",
    "Intenta establecer una rutina de sueño regular y hacer ejercicio moderado."
  ]
}
```

---

### 5. PUT `/mood/{entry_id}` - Actualizar registro

**Request:**
```json
{
  "mood": 2,
  "note": "Actualicé mi nota después de reflexionar"
}
```

**Response:** (200 OK)
```json
{
  "message": "Registro actualizado correctamente",
  "id": 5
}
```

---

### 6. DELETE `/mood/{entry_id}` - Eliminar registro

**Response:** (200 OK)
```json
{
  "message": "Registro eliminado correctamente",
  "id": 5
}
```

---

## Generación de Insights (Lógica de Negocio)

### Algoritmos de análisis

#### 1. Tendencia general (`mood_trend`)
```python
if avg_mood < 1.5:
    trend = "positivo"
elif avg_mood <= 2.0:
    trend = "neutral"
else:
    trend = "negativo"
```

#### 2. Evolución mensual
- Compara promedio del mes actual con el anterior
- Detecta mejoras (+0.3) o empeoramientos (-0.3)
- Genera mensaje de feedback positivo o alerta

#### 3. Distribución de estados
- Cuenta frecuencia de cada nivel (MoodLevel.MUY_BIEN, BIEN, MAL, MUY_MAL)
- Identifica el estado más común
- Calcula porcentajes

#### 4. Detección de días críticos
- Cuenta registros con `MoodLevel.MUY_MAL` (3)
- Si >= 3 días muy malos → recomienda Línea 113 o OBE

### Recomendaciones automáticas

| Condición | Recomendación |
|-----------|---------------|
| `avg_mood > 2.0` (negativo) | "Considera hablar con un profesional de salud mental de la OBE" |
| `very_bad_days >= 3` | "Contacta a la Línea 113 (opción 5) - 24/7 gratuito" |
| `avg_mood > 1.5` | "Intenta establecer una rutina de sueño regular y hacer ejercicio" |
| `total_entries < 10` | "Sigue registrando tu ánimo para mejores recomendaciones" |

---

## Integración con Frontend

El frontend (`MoodLogPage.jsx`) ya tiene la interfaz completa. Necesita conectar con estos endpoints:

### Ejemplo de integración con Axios

```javascript
// Registrar mood
const registerMood = async (mood, note) => {
  const response = await axios.post('http://localhost:8000/mood/register', {
    user_id: 'estudiante_123', // TODO: obtener del contexto de auth
    mood: mood,
    note: note
  });
  return response.data;
};

// Obtener calendario
const getCalendar = async (year, month) => {
  const response = await axios.get(
    `http://localhost:8000/mood/calendar/estudiante_123/${year}/${month}`
  );
  return response.data;
};

// Obtener insights
const getInsights = async () => {
  const response = await axios.get(
    'http://localhost:8000/mood/insights/estudiante_123?days=30'
  );
  return response.data;
};
```

---

## Testing

### Pruebas con curl

#### 1. Registrar varios moods
```bash
# Día muy bien
curl -X POST http://localhost:8000/mood/register \
  -H "Content-Type: application/json" \
  -d '{"user_id": "test_user", "mood": 0, "note": "Excelente día"}'

# Día bien
curl -X POST http://localhost:8000/mood/register \
  -H "Content-Type: application/json" \
  -d '{"user_id": "test_user", "mood": 1, "note": "Tranquilo"}'

# Día mal
curl -X POST http://localhost:8000/mood/register \
  -H "Content-Type: application/json" \
  -d '{"user_id": "test_user", "mood": 2, "note": "Estresante"}'
```

#### 2. Ver historial
```bash
curl http://localhost:8000/mood/history/test_user?days=7
```

#### 3. Ver insights
```bash
curl http://localhost:8000/mood/insights/test_user?days=30
```

#### 4. Ver calendario
```bash
curl http://localhost:8000/mood/calendar/test_user/2026/7
```

---

## Próximas Mejoras (Opcionales)

### 1. Agente Analítico con IA
- Crear `InsightsAnalyzerAgent` que use Gemini para insights personalizados
- Detectar patrones temporales (peor los lunes, mejor los fines de semana)
- Correlacionar con eventos académicos (fechas de exámenes)

### 2. Autenticación
- Integrar con JWT o sesiones
- Reemplazar `user_id` manual con usuario autenticado

### 3. Notificaciones
- Recordatorio diario para registrar mood
- Alerta si detecta patrón negativo persistente (7+ días malos)

### 4. Exportación de datos
- Endpoint para descargar CSV con historial completo
- Gráficos visuales generados en el backend (matplotlib)

---

## Estado de la Funcionalidad 2

| Componente | Estado |
|------------|--------|
| **Modelos de dominio** | ✅ Completo |
| **Port de repositorio** | ✅ Completo |
| **Adapter SQLite** | ✅ Completo |
| **Casos de uso (6)** | ✅ Completo |
| **API Router (6 endpoints)** | ✅ Completo |
| **Bootstrap en main.py** | ✅ Completo |
| **Documentación** | ✅ Completo |
| **Integración frontend** | ⏳ Pendiente (conectar API) |
| **Agente IA para insights** | 🔄 Opcional (futuro) |

---

## Logs de Startup

Al iniciar el servidor, deberías ver:

```
[Startup] Inicializando Dashboard de Bienestar...
[Startup] SQLiteMoodLogRepository inicializado: fisiagent.db
[Startup] Base de datos mood_entries inicializada
[Startup] ✓ Dashboard de Bienestar inicializado (SQLite)
[Startup] 🚀 FISIAgent listo
[Startup] 📊 Funcionalidades:
[Startup]    ✅ Funcionalidad 1: Chat de Apoyo Emocional (RAG + Agentes)
[Startup]    ✅ Funcionalidad 2: Dashboard de Bienestar (SQLite)
```

---

## Arquitectura Hexagonal Aplicada

**Beneficios en esta funcionalidad:**

1. **Independencia de la DB:** Cambiar de SQLite a PostgreSQL = solo crear nuevo adapter
2. **Testeable:** Mockear `MoodLogRepositoryPort` para tests unitarios
3. **Separación clara:** Dominio (mood_models.py) no conoce SQLite
4. **Reutilizable:** Los use cases pueden ser llamados desde REST, GraphQL, CLI, etc.

**Flujo de una petición:**

```
HTTP POST /mood/register
    ↓
mood_router.py (Adapter Inbound)
    ↓
RegisterMoodUseCase (Core)
    ↓
MoodLogRepositoryPort (Interface)
    ↓
SQLiteMoodLogRepository (Adapter Outbound)
    ↓
SQLite DB (fisiagent.db)
```

Cada capa solo conoce la interfaz de la capa adyacente, no su implementación. 🎯
