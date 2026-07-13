import React from 'react';
import logoFisi from '../assets/Logo-fisi.png';

function Message({ message }) {
  const isUser = message.sender === 'user';

  return (
    <div className={`message ${isUser ? 'user-message' : 'bot-message'}`}>
      <div className="message-avatar">
        {isUser ? '👤' : <img src={logoFisi} alt="FISI" className="avatar-logo" />}
      </div>
      <div className="message-bubble">
        <div className="message-text">{message.text}</div>
        <div className="message-time">{message.time}</div>
      </div>
    </div>
  );
}

export default Message;