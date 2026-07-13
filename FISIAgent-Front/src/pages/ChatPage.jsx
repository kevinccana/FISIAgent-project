import React, { useState, useRef, useEffect } from 'react';
import Message from '../components/Message';
import CrisisOverlay from '../components/CrisisOverlay';
import VideoPopup from '../components/VideoPopup';
import { sendMessage } from '../services/api';
import logoFisi from '../assets/Logo-fisi.png';

function ChatPage() {
  const [messages, setMessages] = useState([
    {
      id: 1,
      sender: 'bot',
      text: "Hola, soy FISIAgent, tu asistente de ayuda académica. ¿En qué puedo ayudarte hoy?",
      time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    }
  ]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [showCrisisOverlay, setShowCrisisOverlay] = useState(false);
  const [crisisInfo, setCrisisInfo] = useState(null);
  const [nivelRiesgo, setNivelRiesgo] = useState(null);
  const [showVideoPopup, setShowVideoPopup] = useState(false);
  const [videoSugerido, setVideoSugerido] = useState(null);
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  // Auto-scroll al último mensaje
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Auto-focus al input
  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  const handleSendMessage = async () => {
    if (!inputValue.trim()) return;
  
    // 1. Crear el nuevo mensaje del usuario con la estructura de tu UI
    const userMessage = {
      id: messages.length + 1,
      sender: 'user',
      text: inputValue,
      time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };
  
    // Actualizar la interfaz de inmediato para que el usuario vea su mensaje
    setMessages(prev => [...prev, userMessage]);
    const currentInputValue = inputValue; // Guardamos el valor actual antes de borrarlo
    setInputValue('');
    setIsLoading(true);
  
    try {
      // 2. FORMATEO CLAVE: Convertimos tus mensajes previos al formato de Gemini
      // Mapeamos 'user' -> 'user' y 'bot' -> 'model'
      const formattedHistory = messages.map(msg => ({
        role: msg.sender === 'user' ? 'user' : 'model',
        text: msg.text
      }));
  
      // 3. Enviar al backend el historial formateado y el mensaje de texto actual
      const response = await sendMessage(formattedHistory, currentInputValue);
      
      // Actualizar indicador de nivel de riesgo (BETO)
      if (response.nivel_riesgo) {
        setNivelRiesgo(response.nivel_riesgo);
      }

      // Mostrar VideoPopup si BETO detectó nivel moderado
      if (response.nivel_riesgo === 'moderado' && response.video_sugerido) {
        setVideoSugerido(response.video_sugerido);
        setShowVideoPopup(true);
      }

      // Activar CrisisOverlay si BETO detectó nivel crítico
      if (response.crisis_detected) {
        setCrisisInfo({
          message: response.response,
          contact: {
            name: "LÍNEA 113",
            number: "113",
            extension: "5"
          }
        });
        setShowCrisisOverlay(true);
      }
      
      // 4. Agregar respuesta del bot a la interfaz
      const botMessage = {
        id: Date.now(), // Usar Date.now() evita problemas si hay renders muy rápidos
        sender: 'bot',
        text: response.response,
        time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      };
      
      setMessages(prev => [...prev, botMessage]);
      
    } catch (error) {
      console.error('Error al enviar mensaje:', error);
      const errorMessage = {
        id: Date.now() + 1,
        sender: 'bot',
        text: "Lo siento, estoy teniendo problemas técnicos. Por favor, intenta de nuevo más tarde.",
        time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };
  

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const handleSOSClick = () => {
    setCrisisInfo({
      message: "No estás solo/a. Comunícate ahora:",
      contact: {
        name: "LÍNEA 113 • Salud Mental • Opción 5",
        number: "113",
        extension: "5"
      }
    });
    setShowCrisisOverlay(true);
  };

  return (
    <>
      <div className="chat-container">
        {/* Header con hora, indicador de riesgo y botón SOS */}
        <div className="chat-header">
          <div className="chat-header-left">
            <img src={logoFisi} alt="FISI" className="logo-small" />
            <span className="session-info">sesión #001 - iniciada {new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
          </div>
          <div className="chat-header-right">
            {nivelRiesgo && (
              <div className={`risk-indicator risk-indicator--${nivelRiesgo}`}>
                <span className="risk-dot" />
                <span className="risk-label">
                  {nivelRiesgo === 'control'  && 'Control'}
                  {nivelRiesgo === 'moderado' && 'Moderado'}
                  {nivelRiesgo === 'critico'  && 'Crítico'}
                </span>
              </div>
            )}
            <button className="sos-button" onClick={handleSOSClick}>
              🆘 SOS
            </button>
          </div>
        </div>

        {/* Mensajes del chat */}
        <div className="messages-area">
          {messages.map((msg) => (
            <Message key={msg.id} message={msg} />
          ))}
          {isLoading && (
            <div className="typing-indicator">
              <span>FISIAgent está escribiendo</span>
              <div className="dots">
                <span>.</span><span>.</span><span>.</span>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Input area */}
        <div className="input-area">
          <textarea
            ref={inputRef}
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Escribe tu mensaje..."
            rows={1}
          />
          <button 
            onClick={handleSendMessage} 
            disabled={isLoading || !inputValue.trim()}
            className="send-button"
          >
            ➤
          </button>
        </div>
      </div>

      {/* Video Popup — nivel moderado */}
      {showVideoPopup && (
        <VideoPopup
          video={videoSugerido}
          onClose={() => setShowVideoPopup(false)}
        />
      )}

      {/* Crisis Overlay — nivel crítico */}
      {showCrisisOverlay && (
        <CrisisOverlay
          info={crisisInfo}
          onClose={() => setShowCrisisOverlay(false)}
        />
      )}
    </>
  );
}

export default ChatPage;