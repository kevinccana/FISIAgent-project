import React, { useState } from 'react';

function ResourcesPage() {
  const [searchTerm, setSearchTerm] = useState('');

  // Datos de recursos
  const videosCalma = [
    {
      id: 1,
      titulo: "Ejercicio de Respiración 4-7-8",
      descripcion: "Técnica de respiración para calmar la ansiedad",
      url: "https://www.youtube.com/watch?v=EGO5m_DBzF8&t=96s",
      tipo: "youtube"
    },
    {
      id: 2,
      titulo: "Mindfulness para principiantes",
      descripcion: "5 minutos de atención plena",
      url: "https://www.youtube.com/watch?v=3oCC4NDgYrY&t=17s",
      tipo: "youtube"
    },
    {
      id: 3,
      titulo: "Meditación para dormir",
      descripcion: "Relajación profunda para conciliar el sueño",
      url: "https://www.youtube.com/watch?v=vFrHhwCOaW0",
      tipo: "youtube"
    }
  ];

  const ejerciciosRespiración = [
    {
      id: 7,
      titulo: "Música Relajante",
      descripcion: "Playlist para calmar la mente",
      url: "https://open.spotify.com/embed/playlist/37i9dQZF1DX3Ogo9pFvBkY",
      tipo: "spotify"
    },
    {
      id: 8,
      titulo: "Sonidos de la naturaleza",
      descripcion: "Ambientes para meditar",
      url: "https://www.youtube.com/watch?v=7Ilu033ydSw",
      tipo: "youtube"
    }
  ];

  // Filtrar recursos según búsqueda
  const filtrarPorBusqueda = (items) => {
    if (!searchTerm) return items;
    return items.filter(item =>
      item.titulo.toLowerCase().includes(searchTerm.toLowerCase()) ||
      item.descripcion.toLowerCase().includes(searchTerm.toLowerCase())
    );
  };

  return (
    <div className="resources-page">
      {/* Header con título */}
      <div className="resources-header">
        <h2 className="resources-title">Recursos de Apoyo</h2>
        <p className="resources-subtitle">Encuentra herramientas para tu bienestar emocional</p>
      </div>

      {/* Buscador */}
      <div className="search-container">
        <div className="search-box">
          <span className="search-icon">🔍</span>
          <input
            type="text"
            className="search-input"
            placeholder="Buscar recursos..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
          {searchTerm && (
            <button className="search-clear" onClick={() => setSearchTerm('')}>
              ✕
            </button>
          )}
        </div>
      </div>

      {/* Sección: Videos de Calma */}
      <section className="resources-section">
        <div className="section-header">
          <span className="section-icon">🎬</span>
          <h3 className="section-title">Videos de Calma</h3>
        </div>
        <div className="resources-grid">
          {filtrarPorBusqueda(videosCalma).map(video => (
            <div key={video.id} className="resource-card video-card">
              <div className="resource-icon">🎥</div>
              <div className="resource-info">
                <h4 className="resource-title">{video.titulo}</h4>
                <p className="resource-description">{video.descripcion}</p>
                <button 
                  className="resource-button"
                  onClick={() => window.open(video.url, '_blank')}
                >
                  Ver video →
                </button>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Sección: Ejercicios de Respiración */}
      <section className="resources-section">
        <div className="section-header">
          <span className="section-icon">🧘</span>
          <h3 className="section-title">Ejercicios de Respiración</h3>
        </div>
        <div className="resources-grid">
          {filtrarPorBusqueda(ejerciciosRespiración).map(ejercicio => (
            <div key={ejercicio.id} className="resource-card">
              <div className="resource-icon">
                {ejercicio.tipo === 'spotify' ? '🎵' : '🧘'}
              </div>
              <div className="resource-info">
                <h4 className="resource-title">{ejercicio.titulo}</h4>
                <p className="resource-description">{ejercicio.descripcion}</p>
                <button 
                  className="resource-button"
                  onClick={() => window.open(ejercicio.url, '_blank')}
                >
                  Reproducir →
                </button>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Líneas de ayuda (destacado) */}
      <section className="help-section">
        <div className="help-card">
          <div className="help-icon">🆘</div>
          <div className="help-content">
            <h3 className="help-title">¿Necesitas hablar con alguien ahora?</h3>
            <p className="help-description">
              Línea gratuita disponible 24/7. Profesionales capacitados para escucharte.
            </p>
            <div className="help-contact" onClick={() => window.location.href = 'tel:113'}>
              <span className="help-number">📞 Línea 113 - Opción 5</span>
              <span className="help-arrow">→</span>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}

export default ResourcesPage;