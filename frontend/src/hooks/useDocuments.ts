import { useState, useEffect, useCallback } from 'react';
import { Document } from '../types';
import { api } from '../services/api';

export const useDocuments = (sessionId: string | null) => {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchDocuments = useCallback(async () => {
    if (!sessionId) {
      setDocuments([]);
      return;
    }
    setIsLoading(true);
    setError(null);
    try {
      const data = await api.getDocuments(sessionId);
      setDocuments(data);
    } catch (err: any) {
      setError(err.message || 'Error loading documents list.');
    } finally {
      setIsLoading(false);
    }
  }, [sessionId]);

  useEffect(() => {
    fetchDocuments();
  }, [fetchDocuments]);

  return {
    documents,
    isLoading,
    error,
    refreshDocuments: fetchDocuments,
  };
};
