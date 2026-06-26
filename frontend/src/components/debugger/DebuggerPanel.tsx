import React, { useEffect, useRef } from 'react';
import { Thought } from '../../types';
import ThoughtStep from './ThoughtStep';
import { Terminal, Activity } from 'lucide-react';

interface DebuggerPanelProps {
  currentThoughts: Thought[];
  isStreaming: boolean;
}

const DebuggerPanel: React.FC<DebuggerPanelProps> = ({
  currentThoughts,
  isStreaming,
}) => {
  const scrollRef = useRef<HTMLDivElement>(null);

  // Auto scroll debugger log to bottom on new thoughts
  useEffect(() => {
    scrollRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [currentThoughts]);

  return (
    <aside className="debugger-panel border-l border-[#21262d]">
      <div className="debugger-header">
        <div className="flex-center">
          <Terminal size={16} className="debugger-header-icon mr-2" />
          <h3 className="debugger-title">Auditor ReAct Chain</h3>
        </div>
        {isStreaming && (
          <div className="status-indicator flex-center">
            <Activity className="animate-spin text-accent mr-1" size={12} />
            <span>Processing...</span>
          </div>
        )}
      </div>

      <div className="thought-stream-viewport">
        {currentThoughts.length === 0 ? (
          <div className="empty-debugger-state flex-center">
            <Terminal size={24} className="empty-icon" />
            <p className="empty-debugger-text">Thought chain idle.</p>
            <span className="empty-debugger-sub">Submit a query to trace real-time agent reasoning.</span>
          </div>
        ) : (
          <div className="thought-steps-list">
            {currentThoughts.map((thought, idx) => (
              <ThoughtStep key={idx} thought={thought} />
            ))}
            <div ref={scrollRef} />
          </div>
        )}
      </div>
    </aside>
  );
};

export default DebuggerPanel;
