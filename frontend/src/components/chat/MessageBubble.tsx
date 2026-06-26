import React from 'react';
import { ChatMessage } from '../../types';
import SourceCitation from './SourceCitation';
import { User, ShieldAlert, Award } from 'lucide-react';

interface MessageBubbleProps {
  message: ChatMessage;
}

const MessageBubble: React.FC<MessageBubbleProps> = ({ message }) => {
  const isUser = message.role === 'user';
  
  // Calculate average confidence from citations if available
  const avgConfidence = message.citations && message.citations.length > 0
    ? message.citations.reduce((acc, c) => acc + c.confidence, 0) / message.citations.length
    : null;

  return (
    <div className={`message-row ${isUser ? 'user-row' : 'assistant-row'}`}>
      <div className="message-wrapper">
        {/* Avatar */}
        <div className={`avatar flex-center ${isUser ? 'user-avatar' : 'assistant-avatar'}`}>
          {isUser ? <User size={14} /> : <ShieldAlert size={14} />}
        </div>

        {/* Message Bubble content */}
        <div className="message-bubble-content">
          <div className="message-body">
            {message.content ? (
              // Simple text formatting: convert newlines and markdown-like links to structured lines
              message.content.split('\n').map((line, idx) => {
                // Heuristic regex to parse markdown-like bold text: **text**
                const parts = line.split(/(\*\*.*?\*\*)/g);
                return (
                  <p key={idx} className="message-line">
                    {parts.map((part, pIdx) => {
                      if (part.startsWith('**') && part.endsWith('**')) {
                        return <strong key={pIdx}>{part.slice(2, -2)}</strong>;
                      }
                      return part;
                    })}
                  </p>
                );
              })
            ) : (
              <span className="streaming-cursor">█</span>
            )}
          </div>

          {/* Audit Metrics / Confidence Score */}
          {!isUser && avgConfidence !== null && (
            <div className="audit-metrics">
              <div className="confidence-label flex-center">
                <Award size={14} className="metric-icon" />
                <span>Confidence:</span>
                <span className="confidence-value">
                  {Math.round(avgConfidence * 100)}%
                </span>
              </div>
              <div className="confidence-meter-bg">
                <div 
                  className={`confidence-meter-bar ${
                    avgConfidence >= 0.9 ? 'high' : avgConfidence >= 0.7 ? 'medium' : 'low'
                  }`}
                  style={{ width: `${avgConfidence * 100}%` }}
                />
              </div>
            </div>
          )}

          {/* Source Citations grid */}
          {!isUser && message.citations && message.citations.length > 0 && (
            <div className="citations-section">
              <h4 className="citations-title">Verified Citations ({message.citations.length})</h4>
              <div className="citations-grid">
                {message.citations.map((cite, idx) => (
                  <SourceCitation key={idx} citation={cite} />
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default MessageBubble;
