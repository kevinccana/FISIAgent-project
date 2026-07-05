import { useState } from "react";
import M1 from "../../src/assets/spritePics/M1.png"
import M2 from "../../src/assets/spritePics/M2.png"
import M3 from "../../src/assets/spritePics/M3.png"
import M4 from "../../src/assets/spritePics/M4.png"


// ── Mock Data ────────────────────────────────────────────────────────────────
// mood: 0=Muy bien 1=Bien 2=Mal 3=Muy mal  (ordinal, de mejor a peor)
const MOCK_DATA = {
  year: 2025,
  month: 5, // Mayo (1-indexed)
  entries: {
    1:  { mood: 0, note: "Gran día con amigos" },
    2:  { mood: 1, note: "Tranquilo y productivo" },
    3:  { mood: 0, note: "Me sentí con energía" },
    4:  { mood: 1, note: "" },
    5:  { mood: 2, note: "Un poco cansado" },
    6:  { mood: 0, note: "Excelente inicio de semana" },
    7:  { mood: 1, note: "" },
    8:  { mood: 1, note: "Normal" },
    9:  { mood: 2, note: "Estrés en el trabajo" },
    10: { mood: 3, note: "Muy difícil hoy" },
    11: { mood: 2, note: "Mejorando un poco" },
    12: { mood: 1, note: "" },
    13: { mood: 0, note: "Fin de semana genial" },
    14: { mood: 0, note: "Descansé bien" },
    15: { mood: 1, note: "" },
    16: { mood: 1, note: "Día normal" },
    17: { mood: 2, note: "Cansancio acumulado" },
    18: { mood: 1, note: "" },
    19: { mood: 0, note: "Salida con familia" },
    20: { mood: 1, note: "" },
    21: { mood: 2, note: "Lunes pesado" },
    22: { mood: 1, note: "" },
    23: { mood: 0, note: "Noticias buenas" },
    24: { mood: 1, note: "" },
    25: { mood: 1, note: "" },
    26: { mood: 2, note: "Reuniones largas" },
    27: { mood: 3, note: "Mal día" },
    28: { mood: 1, note: "Recuperándome" },
    29: { mood: 0, note: "¡Mucho mejor!" },
    30: { mood: 1, note: "" },
  },
  // Historial de los últimos 4 meses para gráfico de línea
  monthlyHistory: [
    { label: "Feb", avgMood: 1.2 },
    { label: "Mar", avgMood: 0.8 },
    { label: "Abr", avgMood: 1.5 },
    { label: "May", avgMood: 1.1 },
  ],
};

// ── Mood Config ──────────────────────────────────────────────────────────────
const MOODS = [
  { label: "Muy bien", emoji: "😊", color: "#4A90E2", value: 0, dir: M1},
  { label: "Bien",     emoji: "🙂", color: "#F5C842", value: 1, dir: M2},
  { label: "Mal",      emoji: "😟", color: "#FF8C61", value: 2, dir: M3},
  { label: "Muy mal",  emoji: "😢", color: "#FF4444", value: 3, dir: M4},
];

// ── Helpers ──────────────────────────────────────────────────────────────────
const DAY_LABELS = ["L", "M", "M", "J", "V", "S", "D"];

function buildCalendarGrid(year, month) {
  // month: 1-indexed
  const firstDay = new Date(year, month - 1, 1).getDay(); // 0=Sun
  const offset = (firstDay + 6) % 7; // shift so Mon=0
  const daysInMonth = new Date(year, month, 0).getDate();
  const cells = [];
  for (let i = 0; i < offset; i++) cells.push(null);
  for (let d = 1; d <= daysInMonth; d++) cells.push(d);
  return cells;
}

// ── Mini Bar Chart (SVG) ─────────────────────────────────────────────────────
function BarChart({ entries }) {
  const counts = [0, 0, 0, 0];
  Object.values(entries).forEach(({ mood }) => counts[mood]++);
  const max = Math.max(...counts, 1);
  const W = 180, H = 100, barW = 28, gap = 12;

  return (
    <svg width={W} height={H} style={{ overflow: "visible" }}>
      {counts.map((c, i) => {
        const barH = (c / max) * (H - 20);
        const x = i * (barW + gap) + 10;
        return (
          <g key={i}>
            <rect
              x={x} y={H - barH - 16} width={barW} height={barH}
              rx={4} fill={MOODS[i].color} opacity={0.85}
            />
            <text x={x + barW / 2} y={H - 2} textAnchor="middle"
              fill="#a0a0a0" fontSize={10}>{i + 1}</text>
          </g>
        );
      })}
      {/* y-axis labels */}
      {[0, Math.round(max / 2), max].map((v, i) => (
        <text key={i} x={0} y={H - 16 - (v / max) * (H - 20) + 4}
          fill="#666" fontSize={9} textAnchor="end">{v}</text>
      ))}
    </svg>
  );
}

// ── Mini Line Chart (SVG) ────────────────────────────────────────────────────
function LineChart({ history }) {
  const W = 200, H = 100, pad = 20;
  const vals = history.map(h => h.avgMood);
  const maxV = Math.max(...vals, 2);
  const pts = vals.map((v, i) => {
    const x = pad + (i / (vals.length - 1)) * (W - pad * 2);
    const y = H - pad - (v / maxV) * (H - pad * 2);
    return `${x},${y}`;
  });
  const polyline = pts.join(" ");

  return (
    <svg width={W} height={H} style={{ overflow: "visible" }}>
      {/* grid lines */}
      {[0, 1, 2].map((_, i) => {
        const y = H - pad - (i / 2) * (H - pad * 2);
        return <line key={i} x1={pad} x2={W - pad} y1={y} y2={y}
          stroke="rgba(255,255,255,0.07)" strokeWidth={1} />;
      })}
      {/* area fill */}
      <polyline
        points={`${pad},${H - pad} ${polyline} ${W - pad},${H - pad}`}
        fill="rgba(74,144,226,0.15)" stroke="none"
      />
      {/* line */}
      <polyline points={polyline} fill="none"
        stroke="#4A90E2" strokeWidth={2.5} strokeLinejoin="round" strokeLinecap="round" />
      {/* dots + labels */}
      {vals.map((v, i) => {
        const x = pad + (i / (vals.length - 1)) * (W - pad * 2);
        const y = H - pad - (v / maxV) * (H - pad * 2);
        return (
          <g key={i}>
            <circle cx={x} cy={y} r={4} fill="#4A90E2" stroke="#0f3460" strokeWidth={2} />
            <text x={x} y={H - 4} textAnchor="middle" fill="#a0a0a0" fontSize={9}>
              {history[i].label}
            </text>
          </g>
        );
      })}
      {/* y labels */}
      {[0, 1, 2].map((v, i) => {
        const y = H - pad - (i / 2) * (H - pad * 2);
        return <text key={i} x={pad - 4} y={y + 3} textAnchor="end" fill="#666" fontSize={9}>{v}</text>;
      })}
    </svg>
  );
}

// ── Main Component ────────────────────────────────────────────────────────────
export default function MoodJournalPage() {
  const [data, setData] = useState(MOCK_DATA);
  const [selectedMood, setSelectedMood] = useState(null);
  const [note, setNote] = useState("");
  const [selectedDay, setSelectedDay] = useState(null);

  const { year, month, entries } = data;
  const grid = buildCalendarGrid(year, month);
  const monthName = new Date(year, month - 1, 1)
    .toLocaleString("es-ES", { month: "long", year: "numeric" });

  const handleDayClick = (day) => {
    if (!day) return;
    setSelectedDay(day);
    const entry = entries[day];
    if (entry) {
      setSelectedMood(entry.mood);
      setNote(entry.note);
    } else {
      setSelectedMood(null);
      setNote("");
    }
    console.log(`[MoodJournal] Día seleccionado: ${day}`);
  };

  const handleGuardar = () => {
    if (selectedMood === null) {
      console.warn("[MoodJournal] Guardar sin mood seleccionado");
      return;
    }
    const day = selectedDay ?? new Date().getDate();
    const newEntries = { ...entries, [day]: { mood: selectedMood, note } };
    setData(prev => ({ ...prev, entries: newEntries }));
    console.log(`[MoodJournal] Guardado día ${day}:`, { mood: MOODS[selectedMood].label, note });
    setSelectedMood(null);
    setNote("");
    setSelectedDay(null);
  };

  return (
    <div style={s.page}>
      <h2 style={s.pageTitle}>Interfaz: Registro de Ánimo (Mood Journal)</h2>

      <div style={s.layout}>
        {/* ── Left column: Calendar + Charts ─────────────────────── */}
        <div style={s.leftCol}>

          {/* Calendar */}
          <div style={s.card}>
            <p style={s.monthLabel}>{monthName}</p>
            <div style={s.calGrid}>
              {DAY_LABELS.map((d, i) => (
                <div key={i} style={s.dayHeader}>{d}</div>
              ))}
              {grid.map((day, i) => {
                const entry = day ? entries[day] : null;
                const moodColor = entry ? MOODS[entry.mood].color : null;
                const isSelected = day === selectedDay;
                return (
                  <div
                    key={i}
                    onClick={() => handleDayClick(day)}
                    style={{
                      ...s.dayCell,
                      ...(day ? s.dayCellActive : {}),
                      ...(isSelected ? { outline: `2px solid #4A90E2`, outlineOffset: 2 } : {}),
                    }}
                  >
                    {day && (
                      <>
                        <span style={s.dayNum}>{day}</span>
                        {entry && (
                          <span style={{ 
                            ...s.moodDot, 
                            background: moodColor, 
                            display: 'flex', 
                            justifyContent: 'center', // Centrado horizontal
                            alignItems: 'center'       // Centrado vertical
                          }}>
                            {/* El truco aquí es quitar el height del 75% para que no se estire de forma extraña */}
                            <img src={MOODS[entry.mood].dir} style={{ width: '75%', height: 'auto' }} alt="Mood" />
                          </span>
                        )}
                      </>
                    )}
                  </div>
                );
              })}
            </div>
          </div>

          {/* Charts */}
          <div style={s.card}>
            <p style={s.chartTitle}>Tus ánimos este mes</p>
            <div style={s.chartsRow}>
              <div>
                <p style={s.chartSub}>Tendencia mensual</p>
                <LineChart history={data.monthlyHistory} />
              </div>
              <div style={s.chartDivider} />
              <div>
                <p style={s.chartSub}>Por estado de ánimo</p>
                <BarChart entries={entries} />
              </div>
            </div>
            {/* Legend */}
            <div style={s.legend}>
              {MOODS.map((m, i) => (
                <div key={i} style={s.legendItem}>
                  <div style={{ ...s.legendDot, background: m.color }} />
                  <span style={s.legendLabel}>{i + 1}. {m.label}</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* ── Right column: New Entry ─────────────────────────────── */}
        <div style={s.card}>
          <p style={s.sectionTitle}>Nuevo Registro</p>
          {selectedDay && (
            <p style={s.selectedDayLabel}>Día {selectedDay} de {monthName}</p>
          )}

          <p style={s.fieldLabel}>Mood:</p>
          <div style={s.moodRow}>
            {MOODS.map((m) => (
              <button
                key={m.value}
                onClick={() => {
                  setSelectedMood(m.value);
                  console.log(`[MoodJournal] Mood seleccionado: ${m.label}`);
                }}
                title={m.label}
                style={{
                  ...s.moodBtn,
                  ...(selectedMood === m.value ? {
                    outline: `3px solid ${m.color}`,
                    transform: "scale(1.15)",
                  } : {}),
                }}
              >
                 {/* Emoji <span style={{ fontSize: 28 }}>{m.emoji}</span> */}
                <img style={{}} src={m.dir}></img>

              </button>
            ))}
          </div>

          {selectedMood !== null && (
            <p style={{ ...s.moodSelectedLabel, color: MOODS[selectedMood].color }}>
              {MOODS[selectedMood].label}
            </p>
          )}

          <p style={{ ...s.fieldLabel, marginTop: 14 }}>Notas</p>
          <textarea
            value={note}
            onChange={e => setNote(e.target.value)}
            placeholder="¿Cómo te sientes hoy?"
            style={s.textarea}
          />

          <button
            onClick={handleGuardar}
            style={{
              ...s.saveBtn,
              ...(selectedMood === null ? { opacity: 0.5, cursor: "not-allowed" } : {}),
            }}
          >
            Guardar
          </button>
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
    background: "#0f3460",
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
    flex: 1,
    minWidth: 0,
  },
  card: {
    background: "rgba(255,255,255,0.07)",
    borderRadius: 14,
    padding: "16px 18px",
    border: "1px solid rgba(255,255,255,0.08)",
    minWidth: 200,
  },
  monthLabel: {
    fontSize: 13,
    color: "#a0a0a0",
    textTransform: "capitalize",
    marginBottom: 10,
    textAlign: "center",
  },

  // Calendar
  calGrid: {
    display: "grid",
    gridTemplateColumns: "repeat(7, 1fr)",
    gap: 4,
  },
  dayHeader: {
    textAlign: "center",
    fontSize: 12,
    fontWeight: 600,
    color: "#a0a0a0",
    padding: "4px 0",
  },
  dayCell: {
    minHeight: 44,
    borderRadius: 8,
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    justifyContent: "center",
    gap: 2,
    fontSize: 12,
  },
  dayCellActive: {
    background: "rgba(255,255,255,0.05)",
    cursor: "pointer",
    transition: "background 0.15s",
  },
  dayNum: {
    fontSize: 11,
    color: "#c0c0c0",
    lineHeight: 1,
  },
  moodDot: {
    fontSize: 16,
    lineHeight: 1,
  },

  // Charts
  chartTitle: {
    fontSize: 15,
    fontWeight: 600,
    marginBottom: 12,
    color: "#fff",
  },
  chartSub: {
    fontSize: 11,
    color: "#a0a0a0",
    marginBottom: 6,
  },
  chartsRow: {
    display: "flex",
    gap: 16,
    alignItems: "flex-start",
    flexWrap: "wrap",
  },
  chartDivider: {
    width: 1,
    background: "rgba(255,255,255,0.1)",
    alignSelf: "stretch",
  },
  legend: {
    display: "flex",
    gap: 12,
    flexWrap: "wrap",
    marginTop: 12,
    paddingTop: 10,
    borderTop: "1px solid rgba(255,255,255,0.08)",
  },
  legendItem: {
    display: "flex",
    alignItems: "center",
    gap: 5,
  },
  legendDot: {
    width: 10,
    height: 10,
    borderRadius: "50%",
  },
  legendLabel: {
    fontSize: 11,
    color: "#a0a0a0",
  },

  // New Entry panel
  sectionTitle: {
    fontSize: 16,
    fontWeight: 600,
    marginBottom: 12,
    color: "#ffffff",
  },
  selectedDayLabel: {
    fontSize: 12,
    color: "#4A90E2",
    marginBottom: 10,
    marginTop: -6,
    textTransform: "capitalize",
  },
  fieldLabel: {
    fontSize: 13,
    color: "#c0c0c0",
    marginBottom: 8,
  },
  moodRow: {
    display: "flex",
    gap: 10,
    marginBottom: 4,
  },
  moodBtn: {
    background: "rgba(255,255,255,0.08)",
    border: "none",
    borderRadius: 10,
    padding: "6px 8px",
    cursor: "pointer",
    transition: "all 0.15s",
    outline: "3px solid transparent",
  },
  moodSelectedLabel: {
    fontSize: 12,
    fontWeight: 600,
    marginBottom: 4,
    transition: "color 0.2s",
  },
  textarea: {
    width: "100%",
    minHeight: 90,
    background: "rgba(255,255,255,0.07)",
    border: "1px solid rgba(255,255,255,0.12)",
    borderRadius: 10,
    color: "#e0e0e0",
    fontSize: 13,
    padding: "10px 12px",
    resize: "vertical",
    outline: "none",
    fontFamily: "inherit",
    boxSizing: "border-box",
    marginBottom: 14,
  },
  saveBtn: {
    width: "100%",
    padding: "10px 0",
    background: "#4A90E2",
    border: "none",
    borderRadius: 24,
    color: "#fff",
    fontSize: 14,
    fontWeight: 600,
    cursor: "pointer",
  },
};