import axios from 'axios';

// En build de producción (GitHub Pages) se inyecta VITE_API_URL apuntando al backend
// desplegado (Hugging Face Space). En desarrollo local usa el backend en localhost.
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Servidor frontend: api.js / chatService.js

/**
 * Envía el historial de la conversación al backend de FastAPI.
 * @param {Array} chatHistory - Lista de mensajes previos [{role: "user", text: "..."}, {role: "model", text: "..."}]
 * @param {string} newMessageText - El nuevo mensaje de texto que acaba de escribir el usuario.
 */
export const sendMessage = async (chatHistory, newMessageText) => {
  try {
    // 1. Construimos el historial completo incluyendo el nuevo mensaje del usuario
    const updatedHistory = [
      ...chatHistory,
      { role: "user", text: newMessageText }
    ];

    // 2. Apuntamos a la nueva ruta /chatai enviando el objeto 'history' requerido por FastAPI
    const response = await api.post('/chatai', { 
      history: updatedHistory 
    });

    // 3. Retornamos la respuesta del backend
    // nivel_riesgo viene de BETO: "control" | "moderado" | "critico"
    return {
      response       : response.data.respuesta,
      nivel_riesgo   : response.data.nivel_riesgo,
      video_sugerido : response.data.video_sugerido,
      crisis_detected: response.data.nivel_riesgo === "critico",
    };

  } catch (error) {
    console.error('API Error:', error);
    
    // Respuesta de respaldo en español (acorde a la personalidad del bot) si el backend falla
    return { 
      response: "Estoy aquí para ti. Cuéntame un poco más sobre cómo te estás sintiendo hoy.",
      crisis_detected: false 
    };
  }
};


export const checkHealth = async () => {
  try {
    const response = await api.get('/health');
    return response.data;
  } catch (error) {
    console.error('Health check failed:', error);
    return { status: 'error' };
  }
};

// Visualizador de estado del chatbot: ¿BETO cargó? ¿la API key de Gemini responde?
export const getStatus = async () => {
  try {
    const response = await api.get('/status');
    return response.data;
  } catch (error) {
    console.error('Status check failed:', error);
    return { beto: 'unknown', rag: 'unknown', gemini: 'unknown', gemini_detail: null };
  }
};

// ── Dashboard de Bienestar (Funcionalidad 2: Mood Logs) ─────────────────────

export const registerMood = async (userId, mood, note = '') => {
  const response = await api.post('/mood/register', { user_id: userId, mood, note });
  return response.data;
};

export const getMoodHistory = async (userId, days = 30, limit = null) => {
  const response = await api.get(`/mood/history/${userId}`, {
    params: { days, ...(limit ? { limit } : {}) },
  });
  return response.data;
};

export const getMonthlyCalendar = async (userId, year, month) => {
  const response = await api.get(`/mood/calendar/${userId}/${year}/${month}`);
  return response.data;
};

export const getMoodInsights = async (userId, days = 30) => {
  const response = await api.get(`/mood/insights/${userId}`, { params: { days } });
  return response.data;
};

export const updateMood = async (entryId, mood, note = '') => {
  const response = await api.put(`/mood/${entryId}`, { mood, note });
  return response.data;
};

export const deleteMood = async (entryId) => {
  const response = await api.delete(`/mood/${entryId}`);
  return response.data;
};

// ── Planificador Inteligente (Funcionalidad 3: Tasks) ───────────────────────

export const createTask = async (userId, taskData, autoSuggest = false) => {
  const response = await api.post('/tasks/', {
    user_id: userId,
    priority: null,
    category: 'general',
    estimated_hours: 1.0,
    ...taskData,
    auto_suggest_priority: autoSuggest,
  });
  return response.data;
};

export const getUpcomingTasks = async (userId, days = 7, limit = null) => {
  const response = await api.get(`/tasks/upcoming/${userId}`, {
    params: { days, ...(limit ? { limit } : {}) },
  });
  return response.data;
};

export const getOverdueTasks = async (userId) => {
  const response = await api.get(`/tasks/overdue/${userId}`);
  return response.data;
};

export const getTaskStatistics = async (userId, days = 30) => {
  const response = await api.get(`/tasks/statistics/${userId}`, {
    params: { days },
  });
  return response.data;
};

export const analyzeDailySchedule = async (userId, date) => {
  const response = await api.get(`/tasks/schedule/${userId}/${date}`);
  return response.data;
};

export const getOrganizationSuggestions = async (userId) => {
  const response = await api.get(`/tasks/suggestions/${userId}`);
  return response.data;
};

export const updateTask = async (taskId, updates) => {
  const response = await api.put(`/tasks/${taskId}`, updates);
  return response.data;
};

export const completeTask = async (taskId) => {
  const response = await api.post(`/tasks/${taskId}/complete`);
  return response.data;
};

export const deleteTask = async (taskId) => {
  const response = await api.delete(`/tasks/${taskId}`);
  return response.data;
};

export const createReminder = async (taskId, remindAt, message = '') => {
  const response = await api.post('/tasks/reminders', {
    task_id: taskId,
    remind_at: remindAt,
    message,
  });
  return response.data;
};