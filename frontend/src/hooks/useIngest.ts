import { useState, useCallback } from 'react';
import { IngestProgress } from '../types';

export const useIngest = (sessionId: string | null, onIngestSuccess?: () => void) => {
  const [isUploading, setIsUploading] = useState(false);
  const [progress, setProgress] = useState<Record<string, IngestProgress>>({});
  const [error, setError] = useState<string | null>(null);

  const uploadFiles = useCallback(async (files: File[]) => {
    if (!sessionId) {
      setError('No active session.');
      return;
    }
    
    setIsUploading(true);
    setError(null);
    setProgress({});
    
    // Prepare form data
    const formData = new FormData();
    formData.append('session_id', sessionId);
    files.forEach((file) => formData.append('files', file));
    
    try {
      const response = await fetch('/api/ingest', {
        method: 'POST',
        body: formData,
      });
      
      if (!response.ok) {
        throw new Error(`Upload request failed with status: ${response.status}`);
      }
      
      const reader = response.body?.getReader();
      if (!reader) throw new Error('Readable stream not supported.');
      
      const decoder = new TextDecoder();
      let buffer = '';
      
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        
        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        
        // Save the last partial line back to buffer
        buffer = lines.pop() || '';
        
        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const dataRaw = line.substring(6).trim();
              if (!dataRaw) continue;
              const data = JSON.parse(dataRaw) as IngestProgress;
              
              setProgress((prev) => ({
                ...prev,
                [data.file]: data,
              }));
            } catch (e) {
              // Ignore parse errors on ping/metadata events
            }
          }
        }
      }
      
      if (onIngestSuccess) {
        onIngestSuccess();
      }
    } catch (err: any) {
      setError(err.message || 'Error during file ingestion.');
    } finally {
      setIsUploading(false);
    }
  }, [sessionId, onIngestSuccess]);

  return {
    uploadFiles,
    isUploading,
    progress,
    error,
  };
};
