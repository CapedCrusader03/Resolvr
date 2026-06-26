import React from 'react';
import AppShell from './components/layout/AppShell';
import ChatPanel from './components/chat/ChatPanel';
import { useSession } from './hooks/useSession';
import { useDocuments } from './hooks/useDocuments';
import { useChat } from './hooks/useChat';

const App: React.FC = () => {
  const {
    activeSession,
    sessions,
    selectSession,
    createNewSession,
  } = useSession();

  const {
    documents,
    refreshDocuments,
  } = useDocuments();

  const {
    messages,
    sendMessage,
    isStreaming,
    currentThoughts,
    clearChat,
  } = useChat(activeSession);

  // Trigger refresh of documents list after files uploaded
  const handleIngestSuccess = () => {
    refreshDocuments();
  };

  return (
    <AppShell
      activeSession={activeSession}
      sessions={sessions}
      selectSession={selectSession}
      createNewSession={createNewSession}
      documents={documents}
      refreshDocuments={handleIngestSuccess}
      currentThoughts={currentThoughts}
      isStreaming={isStreaming}
    >
      <ChatPanel
        activeSession={activeSession}
        messages={messages}
        sendMessage={sendMessage}
        isStreaming={isStreaming}
        clearChat={clearChat}
      />
    </AppShell>
  );
};

export default App;
