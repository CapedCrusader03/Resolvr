import React from 'react';
import { ShieldCheck, Bug, BugOff, Plus } from 'lucide-react';

interface HeaderProps {
  activeSession: string | null;
  sessions: string[];
  selectSession: (id: string) => void;
  createNewSession: () => void;
  showDebugger: boolean;
  setShowDebugger: (show: boolean) => void;
}

const Header: React.FC<HeaderProps> = ({
  activeSession,
  sessions,
  selectSession,
  createNewSession,
  showDebugger,
  setShowDebugger,
}) => {
  return (
    <header className="app-header">
      <div className="header-brand">
        <ShieldCheck className="brand-icon" size={24} />
        <span className="brand-name">Resolvr</span>
        <span className="brand-tag">Stateful Auditor</span>
      </div>
      
      <div className="header-actions">
        {/* Session selector */}
        <div className="session-selector-container">
          <select 
            value={activeSession || ''} 
            onChange={(e) => selectSession(e.target.value)}
            className="session-dropdown"
          >
            {sessions.map((sess) => (
              <option key={sess} value={sess}>
                Session: {sess.substring(0, 8)}...
              </option>
            ))}
          </select>
          <button 
            onClick={createNewSession}
            className="btn btn-secondary btn-icon-only"
            title="Create New Session"
          >
            <Plus size={16} />
          </button>
        </div>

        {/* Debugger toggle button */}
        <button
          onClick={() => setShowDebugger(!showDebugger)}
          className={`btn ${showDebugger ? 'btn-active' : 'btn-secondary'} btn-with-icon`}
          title={showDebugger ? "Hide Debugger" : "Show Debugger"}
        >
          {showDebugger ? <BugOff size={16} /> : <Bug size={16} />}
          <span>{showDebugger ? "Close Inspector" : "Inspect Agent"}</span>
        </button>
      </div>
    </header>
  );
};

export default Header;
