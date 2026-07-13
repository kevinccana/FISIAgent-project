import { useEffect, useState } from "react";
import {
  createTask,
  getUpcomingTasks,
  getOverdueTasks,
  getTaskStatistics,
  analyzeDailySchedule,
  getOrganizationSuggestions,
  completeTask,
  deleteTask,
} from "../services/api";

const USER_ID = "estudiante_demo";

const CATEGORIES = ["académico", "personal", "bienestar", "general"];

const EMPTY_FORM = {
  title: "",
  description: "",
  due_date: "",
  category: "académico",
  estimated_hours: 1,
  autoSuggest: true,
};

function todayISODate() {
  return new Date().toISOString().slice(0, 10);
}

export default function TaskPlannerPage() {
  const [upcoming, setUpcoming] = useState([]);
  const [overdue, setOverdue] = useState([]);
  const [stats, setStats] = useState(null);
  const [form, setForm] = useState(EMPTY_FORM);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const [suggestions, setSuggestions] = useState(null);
  const [suggestionsLoading, setSuggestionsLoading] = useState(false);

  const [scheduleDate, setScheduleDate] = useState(todayISODate());
  const [schedule, setSchedule] = useState(null);
  const [scheduleLoading, setScheduleLoading] = useState(false);

  const loadTasks = async () => {
    setLoading(true);
    setError(null);
    try {
      const [up, ov, st] = await Promise.all([
        getUpcomingTasks(USER_ID, 14),
        getOverdueTasks(USER_ID),
        getTaskStatistics(USER_ID, 30),
      ]);
      setUpcoming(up);
      setOverdue(ov);
      setStats(st);
    } catch (e) {
      console.error("[TaskPlanner] Error al cargar tareas:", e);
      setError("No se pudo conectar con el backend. ¿Está corriendo en localhost:8000?");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadTasks();
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!form.title.trim() || !form.due_date) return;

    try {
      await createTask(
        USER_ID,
        {
          title: form.title.trim(),
          description: form.description.trim(),
          due_date: new Date(form.due_date).toISOString(),
          category: form.category,
          estimated_hours: Number(form.estimated_hours) || 1,
        },
        form.autoSuggest
      );
      setForm(EMPTY_FORM);
      await loadTasks();
    } catch (e) {
      console.error("[TaskPlanner] Error al crear tarea:", e);
      setError("No se pudo crear la tarea.");
    }
  };

  const handleComplete = async (taskId) => {
    try {
      await completeTask(taskId);
      await loadTasks();
    } catch (e) {
      console.error("[TaskPlanner] Error al completar tarea:", e);
    }
  };

  const handleDelete = async (taskId) => {
    try {
      await deleteTask(taskId);
      await loadTasks();
    } catch (e) {
      console.error("[TaskPlanner] Error al eliminar tarea:", e);
    }
  };

  const handleGetSuggestions = async () => {
    setSuggestionsLoading(true);
    try {
      const data = await getOrganizationSuggestions(USER_ID);
      setSuggestions(data);
    } catch (e) {
      console.error("[TaskPlanner] Error al obtener sugerencias:", e);
    } finally {
      setSuggestionsLoading(false);
    }
  };

  const handleAnalyzeSchedule = async () => {
    setScheduleLoading(true);
    try {
      const data = await analyzeDailySchedule(USER_ID, scheduleDate);
      setSchedule(data);
    } catch (e) {
      console.error("[TaskPlanner] Error al analizar agenda:", e);
    } finally {
      setScheduleLoading(false);
    }
  };

  const allTasks = [...overdue, ...upcoming];

  return (
    <div style={s.page}>
      <h2 style={s.pageTitle}>Planificador Inteligente</h2>

      {error && <div style={s.errorBanner}>{error}</div>}

      <div style={s.layout}>
        {/* ── Left column: Task list + stats ─────────────────────── */}
        <div style={s.leftCol}>
          {stats && (
            <div style={s.card}>
              <p style={s.sectionTitle}>Estadísticas (30 días)</p>
              <div style={s.statsRow}>
                <div style={s.statBox}>
                  <span style={s.statValue}>{stats.total_tasks}</span>
                  <span style={s.statLabel}>Total</span>
                </div>
                <div style={s.statBox}>
                  <span style={s.statValue}>{stats.completed_tasks}</span>
                  <span style={s.statLabel}>Completadas</span>
                </div>
                <div style={s.statBox}>
                  <span style={s.statValue}>{stats.overdue_tasks}</span>
                  <span style={s.statLabel}>Vencidas</span>
                </div>
                <div style={s.statBox}>
                  <span style={s.statValue}>{stats.completion_percentage}%</span>
                  <span style={s.statLabel}>Completitud</span>
                </div>
              </div>
              <p style={s.trendLabel}>Tendencia: <strong>{stats.productivity_trend}</strong></p>
            </div>
          )}

          <div style={s.card}>
            <p style={s.sectionTitle}>Tus tareas ({allTasks.length})</p>
            {loading && <p style={s.mutedText}>Cargando...</p>}
            {!loading && allTasks.length === 0 && (
              <p style={s.mutedText}>No tienes tareas pendientes. ¡Agrega una!</p>
            )}
            <div style={s.taskList}>
              {allTasks.map((task) => (
                <div key={task.id} style={s.taskItem}>
                  <div style={s.taskHeader}>
                    <span style={s.taskEmoji}>{task.priority_emoji}</span>
                    <span style={s.taskTitle}>{task.title}</span>
                    {task.is_overdue && <span style={s.overdueTag}>VENCIDA</span>}
                  </div>
                  {task.description && <p style={s.taskDesc}>{task.description}</p>}
                  <div style={s.taskMeta}>
                    <span>{task.priority_label}</span>
                    <span>•</span>
                    <span>{task.category}</span>
                    <span>•</span>
                    <span>{task.estimated_hours}h</span>
                    <span>•</span>
                    <span>
                      {task.is_overdue
                        ? `Venció hace ${Math.abs(task.days_until_due)} día(s)`
                        : task.days_until_due === 0
                        ? "Vence hoy"
                        : `Vence en ${task.days_until_due} día(s)`}
                    </span>
                  </div>
                  <div style={s.taskActions}>
                    <button style={s.smallBtn} onClick={() => handleComplete(task.id)}>
                      ✓ Completar
                    </button>
                    <button style={s.smallBtnGhost} onClick={() => handleDelete(task.id)}>
                      Eliminar
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Análisis de agenda diaria (IA) */}
          <div style={s.card}>
            <p style={s.sectionTitle}>Análisis de agenda diaria (IA)</p>
            <div style={s.scheduleRow}>
              <input
                type="date"
                value={scheduleDate}
                onChange={(e) => setScheduleDate(e.target.value)}
                style={s.dateInput}
              />
              <button style={s.smallBtn} onClick={handleAnalyzeSchedule} disabled={scheduleLoading}>
                {scheduleLoading ? "Analizando..." : "Analizar"}
              </button>
            </div>
            {schedule && (
              <div style={s.aiResultBox}>
                <p style={s.mutedText}>
                  {schedule.tasks.length} tarea(s) · {schedule.total_estimated_hours}h estimadas ·{" "}
                  {schedule.is_overloaded ? "⚠️ Sobrecargado" : "Manejable"}
                </p>
                <ul style={s.recList}>
                  {schedule.recommendations.map((r, i) => (
                    <li key={i} style={s.recItem}>{r}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </div>

        {/* ── Right column: New task + AI suggestions ─────────────── */}
        <div style={s.rightCol}>
          <div style={s.card}>
            <p style={s.sectionTitle}>Nueva Tarea</p>
            <form onSubmit={handleSubmit}>
              <p style={s.fieldLabel}>Título</p>
              <input
                style={s.input}
                value={form.title}
                onChange={(e) => setForm({ ...form, title: e.target.value })}
                placeholder="Ej. Entregar proyecto de BD2"
                maxLength={200}
              />

              <p style={s.fieldLabel}>Descripción</p>
              <textarea
                style={s.textarea}
                value={form.description}
                onChange={(e) => setForm({ ...form, description: e.target.value })}
                placeholder="Detalles opcionales..."
                maxLength={1000}
              />

              <p style={s.fieldLabel}>Fecha límite</p>
              <input
                type="datetime-local"
                style={s.input}
                value={form.due_date}
                onChange={(e) => setForm({ ...form, due_date: e.target.value })}
              />

              <div style={s.formRow}>
                <div style={{ flex: 1 }}>
                  <p style={s.fieldLabel}>Categoría</p>
                  <select
                    style={s.input}
                    value={form.category}
                    onChange={(e) => setForm({ ...form, category: e.target.value })}
                  >
                    {CATEGORIES.map((c) => (
                      <option key={c} value={c}>{c}</option>
                    ))}
                  </select>
                </div>
                <div style={{ width: 100 }}>
                  <p style={s.fieldLabel}>Horas</p>
                  <input
                    type="number"
                    min={0.5}
                    step={0.5}
                    style={s.input}
                    value={form.estimated_hours}
                    onChange={(e) => setForm({ ...form, estimated_hours: e.target.value })}
                  />
                </div>
              </div>

              <label style={s.checkboxLabel}>
                <input
                  type="checkbox"
                  checked={form.autoSuggest}
                  onChange={(e) => setForm({ ...form, autoSuggest: e.target.checked })}
                />
                Sugerir prioridad con IA
              </label>

              <button type="submit" style={s.saveBtn}>Crear tarea</button>
            </form>
          </div>

          <div style={s.card}>
            <p style={s.sectionTitle}>Sugerencias de organización (IA)</p>
            <button style={s.smallBtn} onClick={handleGetSuggestions} disabled={suggestionsLoading}>
              {suggestionsLoading ? "Analizando..." : "Analizar mi organización"}
            </button>
            {suggestions && (
              <div style={s.aiResultBox}>
                <p style={s.diagnosisText}>{suggestions.diagnosis}</p>
                <ul style={s.recList}>
                  {suggestions.recommendations.map((r, i) => (
                    <li key={i} style={s.recItem}>{r}</li>
                  ))}
                </ul>
                {suggestions.resources && suggestions.resources.length > 0 && (
                  <>
                    <p style={s.resourcesTitle}>Para investigar por tu cuenta:</p>
                    <div style={s.resourceChips}>
                      {suggestions.resources.map((res, i) => (
                        <a
                          key={i}
                          style={s.resourceChip}
                          href={`https://www.google.com/search?q=${encodeURIComponent(res)}`}
                          target="_blank"
                          rel="noopener noreferrer"
                        >
                          🔎 {res}
                        </a>
                      ))}
                    </div>
                  </>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

// ── Styles ────────────────────────────────────────────────────────────────────
const s = {
  page: {
    flex: 1,
    display: "flex",
    flexDirection: "column",
    padding: "24px 28px",
    background: "#431720",
    overflowY: "auto",
    fontFamily: "'Segoe UI', 'Roboto', sans-serif",
    color: "#e0e0e0",
    minHeight: 0,
  },
  pageTitle: {
    fontSize: 20,
    fontWeight: 600,
    marginBottom: 18,
    color: "#ffffff",
  },
  errorBanner: {
    background: "rgba(255,68,68,0.15)",
    border: "1px solid rgba(255,68,68,0.4)",
    color: "#ff8080",
    borderRadius: 10,
    padding: "10px 14px",
    marginBottom: 14,
    fontSize: 13,
  },
  layout: {
    display: "flex",
    gap: 16,
    flex: 1,
    alignItems: "flex-start",
  },
  leftCol: {
    display: "flex",
    flexDirection: "column",
    gap: 16,
    flex: 1.3,
    minWidth: 0,
  },
  rightCol: {
    display: "flex",
    flexDirection: "column",
    gap: 16,
    flex: 1,
    minWidth: 280,
  },
  card: {
    background: "rgba(255,255,255,0.07)",
    borderRadius: 14,
    padding: "16px 18px",
    border: "1px solid rgba(255,255,255,0.08)",
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: 600,
    marginBottom: 12,
    color: "#ffffff",
  },
  mutedText: {
    fontSize: 13,
    color: "#a0a0a0",
  },

  // Stats
  statsRow: {
    display: "flex",
    gap: 10,
    marginBottom: 8,
  },
  statBox: {
    flex: 1,
    background: "rgba(255,255,255,0.05)",
    borderRadius: 10,
    padding: "10px 8px",
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
  },
  statValue: {
    fontSize: 18,
    fontWeight: 700,
    color: "#B9BEC4",
  },
  statLabel: {
    fontSize: 11,
    color: "#a0a0a0",
    marginTop: 2,
  },
  trendLabel: {
    fontSize: 12,
    color: "#c0c0c0",
  },

  // Task list
  taskList: {
    display: "flex",
    flexDirection: "column",
    gap: 10,
    maxHeight: 420,
    overflowY: "auto",
  },
  taskItem: {
    background: "rgba(255,255,255,0.05)",
    borderRadius: 10,
    padding: "10px 12px",
  },
  taskHeader: {
    display: "flex",
    alignItems: "center",
    gap: 8,
  },
  taskEmoji: {
    fontSize: 15,
  },
  taskTitle: {
    fontSize: 14,
    fontWeight: 600,
    color: "#fff",
    flex: 1,
  },
  overdueTag: {
    fontSize: 10,
    fontWeight: 700,
    color: "#ff4444",
    background: "rgba(255,68,68,0.15)",
    borderRadius: 6,
    padding: "2px 6px",
  },
  taskDesc: {
    fontSize: 12,
    color: "#a0a0a0",
    margin: "4px 0",
  },
  taskMeta: {
    display: "flex",
    gap: 6,
    fontSize: 11,
    color: "#888",
    marginTop: 4,
    flexWrap: "wrap",
  },
  taskActions: {
    display: "flex",
    gap: 8,
    marginTop: 8,
  },

  // Buttons
  smallBtn: {
    background: "#7A7F87",
    border: "none",
    borderRadius: 8,
    color: "#fff",
    fontSize: 12,
    fontWeight: 600,
    padding: "6px 12px",
    cursor: "pointer",
  },
  smallBtnGhost: {
    background: "transparent",
    border: "1px solid rgba(255,255,255,0.2)",
    borderRadius: 8,
    color: "#c0c0c0",
    fontSize: 12,
    padding: "6px 12px",
    cursor: "pointer",
  },
  saveBtn: {
    width: "100%",
    padding: "10px 0",
    background: "#7A7F87",
    border: "none",
    borderRadius: 24,
    color: "#fff",
    fontSize: 14,
    fontWeight: 600,
    cursor: "pointer",
    marginTop: 8,
  },

  // Form
  fieldLabel: {
    fontSize: 12,
    color: "#c0c0c0",
    marginBottom: 6,
    marginTop: 10,
  },
  input: {
    width: "100%",
    background: "rgba(255,255,255,0.07)",
    border: "1px solid rgba(255,255,255,0.12)",
    borderRadius: 8,
    color: "#e0e0e0",
    fontSize: 13,
    padding: "8px 10px",
    outline: "none",
    fontFamily: "inherit",
    boxSizing: "border-box",
  },
  textarea: {
    width: "100%",
    minHeight: 60,
    background: "rgba(255,255,255,0.07)",
    border: "1px solid rgba(255,255,255,0.12)",
    borderRadius: 8,
    color: "#e0e0e0",
    fontSize: 13,
    padding: "8px 10px",
    resize: "vertical",
    outline: "none",
    fontFamily: "inherit",
    boxSizing: "border-box",
  },
  formRow: {
    display: "flex",
    gap: 10,
  },
  checkboxLabel: {
    display: "flex",
    alignItems: "center",
    gap: 8,
    fontSize: 12,
    color: "#c0c0c0",
    marginTop: 12,
  },

  // Schedule / AI
  scheduleRow: {
    display: "flex",
    gap: 8,
    alignItems: "center",
  },
  dateInput: {
    background: "rgba(255,255,255,0.07)",
    border: "1px solid rgba(255,255,255,0.12)",
    borderRadius: 8,
    color: "#e0e0e0",
    fontSize: 13,
    padding: "6px 10px",
    outline: "none",
  },
  aiResultBox: {
    marginTop: 12,
    paddingTop: 10,
    borderTop: "1px solid rgba(255,255,255,0.08)",
  },
  diagnosisText: {
    fontSize: 13,
    color: "#e0e0e0",
    marginBottom: 8,
  },
  recList: {
    margin: 0,
    paddingLeft: 18,
  },
  recItem: {
    fontSize: 12,
    color: "#c0c0c0",
    marginBottom: 6,
  },
  resourcesTitle: {
    fontSize: 12,
    fontWeight: 600,
    color: "#e0e0e0",
    marginTop: 10,
    marginBottom: 8,
  },
  resourceChips: {
    display: "flex",
    flexWrap: "wrap",
    gap: 8,
  },
  resourceChip: {
    fontSize: 11.5,
    color: "#B9BEC4",
    background: "rgba(122,127,135,0.15)",
    border: "1px solid rgba(122,127,135,0.35)",
    borderRadius: 20,
    padding: "5px 12px",
    textDecoration: "none",
    cursor: "pointer",
  },
};
