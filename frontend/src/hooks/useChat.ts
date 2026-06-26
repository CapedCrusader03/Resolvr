import { useState, useCallback } from 'react';
import { ChatMessage, Thought, Citation } from '../types';

export const useChat = (sessionId: string | null) => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [currentThoughts, setCurrentThoughts] = useState<Thought[]>([]);
  const [error, setError] = useState<string | null>(null);

  const sendMessage = useCallback(async (content: string) => {
    if (!sessionId) {
      setError('No active audit session.');
      return;
    }
    
    setIsStreaming(true);
    setError(null);
    setCurrentThoughts([]);
    
    // Add user message to state
    const userMsg: ChatMessage = {
      id: Math.random().toString(),
      role: 'user',
      content,
      timestamp: new Date().toISOString(),
    };
    
    setMessages((prev) => [...prev, userMsg]);
    
    // Setup placeholder message for assistant streaming
    const assistantMsgId = Math.random().toString();
    const placeholderAssistantMsg: ChatMessage = {
      id: assistantMsgId,
      role: 'assistant',
      content: '',
      timestamp: new Date().toISOString(),
      citations: [],
      thoughtLog: [],
    };
    
    setMessages((prev) => [...prev, placeholderAssistantMsg]);
    
    try {
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: content, session_id: sessionId }),
      });
      
      if (!response.ok) {
        throw new Error(`Chat request failed with status: ${response.status}`);
      }
      
      const reader = response.body?.getReader();
      if (!reader) throw new Error('Readable stream not supported.');
      
      const decoder = new TextDecoder();
      let buffer = '';
      
      let accumulatedText = '';
      const accumulatedCitations: Citation[] = [];
      const accumulatedThoughts: Thought[] = [];
      
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
              const event = JSON.parse(dataRaw);
              
              if (event.type === 'answer_chunk') {
                accumulatedText += event.content;
                setMessages((prev) =>
                  prev.map((msg) =>
                    msg.id === assistantMsgId
                      ? { ...msg, content: accumulatedText }
                      : msg
                  )
                );
              } else if (event.type === 'thought') {
                const newThought: Thought = {
                  node: event.node,
                  type: event.thought_type || 'thought',
                  content: event.content,
                  timestamp: new Date().toISOString(),
                };
                accumulatedThoughts.push(newThought);
                setCurrentThoughts([...accumulatedThoughts]);
                
                setMessages((prev) =>
                  prev.map((msg) =>
                    msg.id === assistantMsgId
                      ? { ...msg, thoughtLog: [...accumulatedThoughts] }
                      : msg
                  )
                );
              } else if (event.type === 'citation') {
                const newCitation: Citation = {
                  source_doc_id: event.source_doc_id || '',
                  filename: event.filename,
                  page_number: event.page_number,
                  row_number: event.row_number,
                  confidence: event.confidence || 0.9,
                };
                accumulatedCitations.push(newCitation);
                
                setMessages((prev) =>
                  prev.map((msg) =>
                    msg.id === assistantMsgId
                      ? { ...msg, citations: [...accumulatedCitations] }
                      : msg
                  )
                );
              } else if (event.type === 'error') {
                throw new Error(event.message);
              }
            } catch (e) {
              // Ignore parsing comments
            }
          }
        }
      }
    } catch (err: any) {
      setError(err.message || 'Connection lost.');
      setMessages((prev) =>
        prev.map((msg) =>
          msg.id === assistantMsgId
            ? { ...msg, content: `${msg.content}\n\n*[Connection Error: ${err.message || 'Lost connection to server'}...]*` }
            : msg
        )
      );
    } finally {
      setIsStreaming(false);
    }
  }, [sessionId]);

  const clearChat = useCallback(() => {
    setMessages([]);
    setCurrentThoughts([]);
  }, []);

  return {
    messages,
    sendMessage,
    isStreaming,
    currentThoughts,
    clearChat,
    error,
  };
};
