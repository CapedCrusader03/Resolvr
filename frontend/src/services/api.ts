import { Document } from '../types';

const API_BASE = '/api';

export const api = {
  async createSession(): Promise<string> {
    const res = await fetch(`${API_BASE}/sessions`, { method: 'POST' });
    if (!res.ok) throw new Error('Failed to create audit session.');
    const data = await res.json();
    return data.session_id;
  },

  async getSessions(): Promise<string[]> {
    const res = await fetch(`${API_BASE}/sessions`);
    if (!res.ok) throw new Error('Failed to fetch sessions list.');
    return await res.json();
  },

  async getDocuments(sessionId: string): Promise<Document[]> {
    const res = await fetch(`${API_BASE}/documents?session_id=${sessionId}`);
    if (!res.ok) throw new Error('Failed to fetch documents list.');
    return await res.json();
  },
};
