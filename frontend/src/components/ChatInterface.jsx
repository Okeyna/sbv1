import React, { useState, useEffect, useRef } from 'react';
import * as api from '../api';

const ChatInterface = ({ fileId }) => {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef(null);

  useEffect(() => {
    loadChatHistory();
  }, [fileId]);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const loadChatHistory = async () => {
    try {
      const history = await api.getChatHistory(fileId);
      setMessages(history);
    } catch (err) {
      console.error('Failed to load chat history:', err);
    }
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const handleSend = async () => {
    if (!input.trim()) return;

    const userMessage = { role: 'user', content: input };
    setMessages([...messages, userMessage]);
    setInput('');
    setLoading(true);

    try {
      const response = await api.sendMessage(fileId, input);
      setMessages(prev => [...prev, { role: 'assistant', content: response.response }]);
    } catch (err) {
      console.error('Failed to send message:', err);
      setMessages(prev => [...prev, { role: 'error', content: 'Failed to get response. Please try again.' }]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="chat-interface">
      <h3>AI Tutor Chat</h3>
      <div className="chat-messages">
        {messages.length === 0 ? (
          <p className="empty-state">Ask a question about your study material.</p>
        ) : (
          messages.map((msg, index) => (
            <div
              key={index}
              className={`message ${msg.role === 'user' ? 'user-message' : msg.role === 'error' ? 'error-message' : 'ai-message'}`}
            >
              <div className="message-content">{msg.content}</div>
            </div>
          ))
        )}
        {loading && (
          <div className="message ai-message">
            <div className="message-content loading">Thinking...</div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      <div className="chat-input-area">
        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder="Ask a question about your study material..."
          rows="3"
          disabled={loading}
        />
        <button
          className="btn-primary"
          onClick={handleSend}
          disabled={loading || !input.trim()}
        >
          Send
        </button>
      </div>
    </div>
  );
};

export default ChatInterface;
