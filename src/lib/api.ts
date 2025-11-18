// src/lib/api.ts
// API Client for Gamora AI Backend

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export interface GenerateGameRequest {
  prompt: string;
  title?: string;
  description?: string;
}

export interface GenerateGameResponse {
  project_id: string;
  status: string;
  message: string;
  websocket_url: string;
}

export interface ProjectResponse {
  project_id: string;
  title: string;
  description?: string;
  status: string;
  web_preview_url?: string;
  builds?: Record<string, string>;
  created_at: string;
}

export interface ProgressUpdate {
  type: 'progress' | 'complete' | 'error' | 'connected';
  data: {
    status?: string;
    message?: string;
    progress?: number;
    step?: string;
    web_preview_url?: string;
    builds?: Record<string, string>;
    error?: string;
    project_id?: string;
  };
}

class ApiClient {
  private baseUrl: string;

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl;
  }

  private async getAuthHeaders(): Promise<HeadersInit> {
    const { data: { session } } = await import('@/lib/supabase').then(m => m.supabase.auth.getSession());
    
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
    };

    if (session?.access_token) {
      headers['Authorization'] = `Bearer ${session.access_token}`;
    }

    return headers;
  }

  async generateGame(request: GenerateGameRequest): Promise<GenerateGameResponse> {
    const headers = await this.getAuthHeaders();
    
    const response = await fetch(`${this.baseUrl}/api/v1/generate/game`, {
      method: 'POST',
      headers,
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Failed to generate game' }));
      throw new Error(error.detail || 'Failed to generate game');
    }

    return response.json();
  }

  async getProject(projectId: string): Promise<ProjectResponse> {
    const headers = await this.getAuthHeaders();
    
    const response = await fetch(`${this.baseUrl}/api/v1/projects/${projectId}`, {
      method: 'GET',
      headers,
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Project not found' }));
      throw new Error(error.detail || 'Project not found');
    }

    return response.json();
  }

  async listProjects(limit: number = 50, offset: number = 0): Promise<ProjectResponse[]> {
    const headers = await this.getAuthHeaders();
    
    const response = await fetch(`${this.baseUrl}/api/v1/projects?limit=${limit}&offset=${offset}`, {
      method: 'GET',
      headers,
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Failed to list projects' }));
      throw new Error(error.detail || 'Failed to list projects');
    }

    return response.json();
  }

  async createWebSocketConnection(projectId: string, onMessage: (update: ProgressUpdate) => void): Promise<WebSocket> {
    // Get auth token
    const { data: { session } } = await import('@/lib/supabase').then(m => m.supabase.auth.getSession());
    const token = session?.access_token || '';
    
    // Create WebSocket URL with auth token as query param (backend should handle this)
    const wsProtocol = this.baseUrl.startsWith('https') ? 'wss' : 'ws';
    const wsBase = this.baseUrl.replace(/^https?/, wsProtocol);
    const wsUrl = `${wsBase}/api/v1/generate/ws/${projectId}${token ? `?token=${token}` : ''}`;
    
    const ws = new WebSocket(wsUrl);

    ws.onopen = () => {
      console.log('WebSocket connected');
    };

    ws.onmessage = (event) => {
      try {
        const update: ProgressUpdate = JSON.parse(event.data);
        onMessage(update);
      } catch (error) {
        console.error('Failed to parse WebSocket message:', error);
      }
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };

    ws.onclose = () => {
      console.log('WebSocket disconnected');
    };

    return ws;
  }
}

export const apiClient = new ApiClient();

