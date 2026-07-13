import React, { useState, useRef } from 'react';

function CrisisOverlay({ onClose }) {
  const [showVideo, setShowVideo] = useState(true);
  const [showContact, setShowContact] = useState(false);
  const videoRef = useRef(null);

  // Saltar directamente a los números de emergencia
  const handleSkipToContact = () => {
    // Detener el video si está reproduciéndose
    if (videoRef.current) {
      videoRef.current.pause();
    }
    setShowVideo(false);
    setShowContact(true);
  };

  // Cuando el video termina, lo reinicia (bucle infinito)
  const handleVideoEnd = () => {
    if (videoRef.current) {
      videoRef.current.currentTime = 0;
      videoRef.current.play();
    }
  };

  // Llamar a la línea 113
  const handleCallNow = () => {
    window.location.href = 'tel:113';
  };

  // Pantalla 1: Video calmante (bucle infinito)
  if (showVideo) {
    return (
      <div className="crisis-overlay">
        <div className="crisis-card video-card">
          {/* Header con título y botón cerrar */}
          <div className="crisis-header">
            <div className="header-left">
              <span className="sos-icon">🆘</span>
              <h2>JoinIA</h2>
            </div>
            <button className="close-button" onClick={onClose}>✕</button>
          </div>

          {/* Mensaje de introducción */}
          <p className="intro-message">
            Hola, soy JoinIA. A continuación te mostraré un video tranquilizador.
          </p>

         

          {/* Información del video */}
          <div className="video-info">
            <div className="video-title">
              <span className="video-icon">🧘</span>
              <span>Respiración Guiada para Calmar la Ansiedad</span>
            </div>
            <div className="video-channel">
              <span className="channel-icon">🎧</span>
              <span>JoinIA - Bienestar emocional</span>
            </div>
            <div className="video-actions">
              <span className="live-badge">🔴 Reproduciéndose en bucle</span>
            </div>
          </div>

          {/* Botones de acción */}
          <div className="video-controls">
            <button className="skip-button" onClick={handleSkipToContact}>
              Saltar al contacto de emergencia →
            </button>
          </div>

          {/* Footer */}
          <div className="crisis-footer">
            <span>Respira. Estás a salvo.</span>
          </div>
        </div>
      </div>
    );
  }

  // Pantalla 2: Números de emergencia
  if (showContact) {
    return (
      <div className="crisis-overlay">
        <div className="crisis-card numbers-card">
          <div className="crisis-header">
            <div className="header-left">
              <span className="sos-icon">📞</span>
              <h2>No estás solo/a</h2>
            </div>
            <button className="close-button" onClick={onClose}>✕</button>
          </div>

          <div className="crisis-content">
            <p className="crisis-message">
              Comunícate ahora. Están entrenados para ayudarte.
            </p>

            <div className="crisis-contact" onClick={handleCallNow}>
              <div className="contact-icon">📞</div>
              <div className="contact-details">
                <div className="contact-name">Línea 113 - Salud Mental</div>
                <div className="contact-number">113</div>
                <div className="contact-extension">Marca y pide la opción 5</div>
                <div className="contact-description">Gratuito · 24/7 · Todo el país</div>
              </div>
            </div>

            <p className="alternative-option">
              También puedes acudir al centro de salud más cercano.
            </p>
          </div>

          <button className="close-bottom" onClick={onClose}>
            cerrar
          </button>
        </div>
      </div>
    );
  }

  return null;
}

export default CrisisOverlay;