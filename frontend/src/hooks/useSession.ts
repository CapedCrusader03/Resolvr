import { useState, useEffect, useCallback } from 'react';
import { api } from '../services/api';

export const useSession = () => {
  const [activeSession, setActiveSession] = useState<string | null>(null);
  const [sessions, setSessions] = useState<string[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchSessions = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await api.getSessions();
      setSessions(data);
      // Auto-select latest session if none selected and sessions exist
      const stored = localStorage.getItem('resolvr_session_id');
      if (stored) {
        setActiveSession(stored);
      } else if (data.length > 0) {
        selectSession(data[0]);
      } else {
        await createNewSession();
      }
    } catch (err: any) {
      setError(err.message || 'Error loading sessions.');
    } finally {
      setIsLoading(false);
    }
  }, []);

  const selectSession = useCallback((sessionId: string) => {
    setActiveSession(sessionId);
    localStorage.setItem('resolvr_session_id', sessionId);
  }, []);

  const createNewSession = useCallback(async () => {
    setIsLoading(true);
    try {
      const newId = await api.createSession();
      setSessions((prev) => [newId, ...prev]);
      selectSession(newId);
    } catch (err: any) {
      setError(err.message || 'Error creating new session.');
    } finally {
      setIsLoading(false);
    }
  }, [selectSession]);

  useEffect(() => {
    fetchSessions();
  }, [fetchSessions]);

  return {
    activeSession,
    sessions,
    isLoading,
    error,
    selectSession,
    createNewSession,
    refreshSessions: fetchSessions,
  };
};
