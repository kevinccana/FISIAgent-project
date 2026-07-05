import React from 'react';

const ICONO_TIPO = {
  respiracion: '🫁',
  mindfulness : '🧘',
  relajacion  : '🌿',
};

function VideoPopup({ video, onClose }) {
  if (!video) return null;

  return (
    <div className="video-popup-overlay" onClick={onClose}>
      <div className="video-popup-card" onClick={(e) => e.stopPropagation()}>

        {/* Header */}
        <div className="video-popup-header">
          <span className="video-popup-tag">💙 Recurso de apoyo</span>
          <button className="video-popup-close" onClick={onClose}>✕</button>
        </div>

        {/* Intro */}
        <p className="video-popup-intro">
          Parece que estás pasando por un momento difícil. Te comparto este video que puede ayudarte:
        </p>

        {/* Card del video */}
        <div className="video-popup-info">
          <div className="video-popup-icon">
            {ICONO_TIPO[video.tipo] ?? '🎥'}
          </div>
          <div className="video-popup-details">
            <h4 className="video-popup-titulo">{video.titulo}</h4>
            <p className="video-popup-descripcion">{video.descripcion}</p>
            <span className="video-popup-duracion">⏱ {video.duracion}</span>
          </div>
        </div>

        {/* Acciones */}
        <div className="video-popup-actions">
          <button
            className="video-popup-btn-watch"
            onClick={() => { window.open(video.url, '_blank'); onClose(); }}
          >
            ▶ Ver video ahora
          </button>
          <button className="video-popup-btn-later" onClick={onClose}>
            Quizás luego
          </button>
        </div>

      </div>
    </div>
  );
}

export default VideoPopup;
