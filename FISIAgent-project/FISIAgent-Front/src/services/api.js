import axios from 'axios';

// URL fija mientras pruebas
const API_URL = 'http://localhost:8000';

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