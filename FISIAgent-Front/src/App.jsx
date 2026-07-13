import React, { useState } from 'react';
import ChatPage from './pages/ChatPage';
import MoodLogPage from './pages/MoodLogPage';
import ResourcesPage from './pages/ResourcesPage';
import TaskPlannerPage from './pages/TaskPlannerPage';
import logoFisi from './assets/Logo-fisi.png';
import './styles/global.css';

function App() {
  const [currentPage, setCurrentPage] = useState('chat');

  const renderPage = () => {
    switch(currentPage) {
      case 'chat':
        return <ChatPage />;
      case 'mood':
        return <MoodLogPage />;
      case 'resources':
        return <ResourcesPage />;
      case 'tasks':
        return <TaskPlannerPage />;
      default:
        return <ChatPage />;
    }
  };

  return (
    <div className="app">
      <div className="sidebar">
        <div className="logo-area">
          <img src={logoFisi} alt="FISI" className="logo" />
          <h2>FISIAgent</h2>
          <span className="tagline">ayuda académica y bienestar</span>
        </div>
        
        <nav className="menu">
          <button 
            className={`menu-item ${currentPage === 'chat' ? 'active' : ''}`}
            onClick={() => setCurrentPage('chat')}
          >
            💬 Nuevo Chat
          </button>
          <button 
            className={`menu-item ${currentPage === 'mood' ? 'active' : ''}`}
            onClick={() => setCurrentPage('mood')}
          >
            📊 Registro de Ánimo
          </button>
          <button
            className={`menu-item ${currentPage === 'resources' ? 'active' : ''}`}
            onClick={() => setCurrentPage('resources')}
          >
            📍 Recursos
          </button>
          <button
            className={`menu-item ${currentPage === 'tasks' ? 'active' : ''}`}
            onClick={() => setCurrentPage('tasks')}
          >
            📅 Planificador
          </button>
        </nav>
      </div>
      
      <div className="main-content">
        {renderPage()}
      </div>
    </div>
  );
}

export default App;