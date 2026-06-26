import React, { useState } from 'react';
import Header from './Header';
import Sidebar from '../sidebar/Sidebar';
import DebuggerPanel from '../debugger/DebuggerPanel';
import { Thought } from '../../types';

interface AppShellProps {
  children: React.ReactNode;
  activeSession: string | null;
  sessions: string[];
  selectSession: (id: string) => void;
  createNewSession: () => void;
  documents: any[];
  refreshDocuments: () => void;
  currentThoughts: Thought[];
  isStreaming: boolean;
}

const AppShell: React.FC<AppShellProps> = ({
  children,
  activeSession,
  sessions,
  selectSession,
  createNewSession,
  documents,
  refreshDocuments,
  currentThoughts,
  isStreaming,
}) => {
  const [showDebugger, setShowDebugger] = useState(true);

  return (
    <div className="app-container">
      {/* Header */}
      <Header
        activeSession={activeSession}
        sessions={sessions}
        selectSession={selectSession}
        createNewSession={createNewSession}
        showDebugger={showDebugger}
        setShowDebugger={setShowDebugger}
      />
      
      {/* Body content */}
      <div className="main-content">
        {/* Left Sidebar */}
        <Sidebar
          activeSession={activeSession}
          documents={documents}
          refreshDocuments={refreshDocuments}
        />
        
        {/* Main Chat Panel */}
        <main className="chat-container">
          {children}
        </main>
        
        {/* Right Debugger Panel */}
        {showDebugger && (
          <DebuggerPanel
            currentThoughts={currentThoughts}
            isStreaming={isStreaming}
          />
        )}
      </div>
    </div>
  );
};

export default AppShell;
