import React, { useState, KeyboardEvent } from 'react';
import { Send, Loader } from 'lucide-react';

interface ChatInputProps {
  onSend: (text: string) => void;
  disabled: boolean;
  isStreaming: boolean;
}

const ChatInput: React.FC<ChatInputProps> = ({
  onSend,
  disabled,
  isStreaming,
}) => {
  const [text, setText] = useState('');

  const handleSend = () => {
    if (text.trim() && !disabled) {
      onSend(text.trim());
      setText('');
    }
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="chat-input-panel border-t border-[#21262d]">
      <div className="input-wrapper glass">
        <textarea
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={disabled ? "Please upload documents to query..." : "Ask Auditor (e.g. 'Sum all restaurant bills')"}
          className="prompt-textarea"
          rows={1}
          disabled={disabled}
        />
        
        <button
          onClick={handleSend}
          disabled={disabled || !text.trim() || isStreaming}
          className="send-button flex-center accent-glow-hover"
        >
          {isStreaming ? (
            <Loader className="animate-spin" size={16} />
          ) : (
            <Send size={16} />
          )}
        </button>
      </div>
      <div className="input-footer-hint">
        Press Enter to submit, Shift+Enter for new line. Decimal-safe safe math engine active.
      </div>
    </div>
  );
};

export default ChatInput;
