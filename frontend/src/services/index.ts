import type { User, TokenPair, Note, Notebook, Workflow } from '@/types';
import api from './api';

export const authService = {
  async login(email: string, password: string): Promise<TokenPair & { user: User }> {
    return api.post('/auth/login', { email, password });
  },

  async register(email: string, password: string, username: string): Promise<{ user: User }> {
    return api.post('/auth/register', { email, password, username });
  },

  async logout(): Promise<void> {
    try {
      await api.post('/auth/logout');
    } finally {
      api.logout();
    }
  },

  async refreshToken(): Promise<TokenPair> {
    return api.post('/auth/refresh');
  },

  async getCurrentUser(): Promise<User> {
    return api.get('/auth/me');
  },

  async updateProfile(data: Partial<User>): Promise<User> {
    return api.put('/auth/profile', data);
  },
};

export const noteService = {
  async getNotes(params?: { page?: number; limit?: number; search?: string; tag?: string }): Promise<{ items: Note[]; total: number }> {
    return api.get('/notes', params);
  },

  async getNote(id: string): Promise<Note> {
    return api.get(`/notes/${id}`);
  },

  async createNote(data: { title: string; content: string; tags?: string[]; notebook_id?: string; is_public?: boolean }): Promise<Note> {
    return api.post('/notes', data);
  },

  async updateNote(id: string, data: Partial<Note>): Promise<Note> {
    return api.put(`/notes/${id}`, data);
  },

  async deleteNote(id: string): Promise<void> {
    return api.delete(`/notes/${id}`);
  },

  async getNoteVersions(id: string): Promise<Note[]> {
    return api.get(`/notes/${id}/versions`);
  },
};

export const notebookService = {
  async getNotebooks(): Promise<Notebook[]> {
    return api.get('/notebooks');
  },

  async getNotebook(id: string): Promise<Notebook> {
    return api.get(`/notebooks/${id}`);
  },

  async createNotebook(data: { name: string; description?: string; color?: string; icon?: string; parent_id?: string }): Promise<Notebook> {
    return api.post('/notebooks', data);
  },

  async updateNotebook(id: string, data: Partial<Notebook>): Promise<Notebook> {
    return api.put(`/notebooks/${id}`, data);
  },

  async deleteNotebook(id: string): Promise<void> {
    return api.delete(`/notebooks/${id}`);
  },
};

export const workflowService = {
  async getWorkflows(): Promise<Workflow[]> {
    return api.get('/workflows');
  },

  async getWorkflow(id: string): Promise<Workflow> {
    return api.get(`/workflows/${id}`);
  },

  async createWorkflow(data: { name: string; description?: string; trigger_type: string; steps: unknown[] }): Promise<Workflow> {
    return api.post('/workflows', data);
  },

  async updateWorkflow(id: string, data: Partial<Workflow>): Promise<Workflow> {
    return api.put(`/workflows/${id}`, data);
  },

  async deleteWorkflow(id: string): Promise<void> {
    return api.delete(`/workflows/${id}`);
  },

  async executeWorkflow(id: string): Promise<{ execution_id: string }> {
    return api.post(`/workflows/${id}/execute`);
  },
};
