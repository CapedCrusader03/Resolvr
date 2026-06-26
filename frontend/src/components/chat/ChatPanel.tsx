import React, { useEffect, useRef } from 'react';
import MessageBubble from './MessageBubble';
import ChatInput from './ChatInput';
import { Sparkles, Terminal } from 'lucide-react';

interface ChatPanelProps {
  activeSession: string | null;
  messages: any[];
  sendMessage: (text: string) => Promise<void>;
  isStreaming: boolean;
}

const ChatPanel: React.FC<ChatPanelProps> = ({
  activeSession,
  messages,
  sendMessage,
  isStreaming,
}) => {
  const bottomRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom of chat
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleQuerySend = (text: string) => {
    sendMessage(text);
  };

  const sampleQueries = [
    "Sum all Stripe receipts from software subscriptions",
    "Do my credit card expenses match the invoice totals?",
    "Find duplicate restaurant transactions from last week",
    "List transactions categorized as travel expenses"
  ];

  return (
    <div className="chat-panel-container">
      {/* Empty onboarding state */}
      {messages.length === 0 ? (
        <div className="onboarding-container">
          <div className="brand-badge flex-center">
            <Sparkles size={16} className="badge-icon glow-badge" />
            <span>Agentic Audit Assistant</span>
          </div>
          
          <h2 className="onboarding-title">How can I help audit your books?</h2>
          <p className="onboarding-subtitle">
            Upload receipts, bank statement PDFs, or Excel dumps in the sidebar. 
            Ask me to calculate totals, scan for duplicates, or flag layout anomalies.
          </p>

          <div className="suggestions-grid">
            {sampleQueries.map((query) => (
              <button
                key={query}
                onClick={() => handleQuerySend(query)}
                className="suggestion-chip glass glass-interactive"
                disabled={!activeSession || isStreaming}
              >
                <Terminal size={14} className="chip-icon" />
                <span>{query}</span>
              </button>
            ))}
          </div>
        </div>
      ) : (
        /* Scrollable Message List */
        <div className="message-list-viewport">
          {messages.map((msg) => (
            <MessageBubble key={msg.id} message={msg} />
          ))}
          <div ref={bottomRef} />
        </div>
      )}

      {/* Input panel fixed at bottom */}
      <ChatInput 
        onSend={handleQuerySend} 
        disabled={!activeSession || isStreaming} 
        isStreaming={isStreaming} 
      />
    </div>
  );
};

export default ChatPanel;
