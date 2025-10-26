/**
 * API Client for BGB Chat Backend
 */

// Base URL for the API
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8080';
const API_PREFIX = '/api/v1';

// Types
export interface ToolCall {
  name: string;
  arguments: string | any;
  result?: string | any;
}

export interface Thread {
  id: string;
  title: string | null;
  thread_metadata: Record<string, any>;
  created_at: string;
  updated_at: string;
  deleted_at: string | null;
}

export interface Message {
  id: number;
  thread_id: string;
  role: 'user' | 'assistant' | 'tool';
  content: string;
  agent_name: string | null;
  tool_calls: ToolCall[] | null;
  usage: any | null;
  created_at: string;
}

export interface Agent {
  name: string;
  description: string;
  available: boolean;
}

export interface CreateThreadRequest {
  title?: string;
  thread_metadata?: Record<string, any>;
}

export interface SendMessageRequest {
  agent: string;
  input: string;
  params?: Record<string, any>;
  stream?: boolean;
}

export interface SendMessageResponse {
  message: Message;
  usage?: any;
  tool_calls?: any[];
  meta?: Record<string, any>;
}

// Stream Events
export type StreamEvent =
  | { type: 'metadata'; data: { thread_id: string } }
  | { type: 'start'; data: { role: string; agent: string } }
  | { type: 'thinking'; data: { status: 'processing' | 'done' } }
  | { type: 'token'; data: { token: string } }
  | { type: 'tool_call'; data: any }
  | { type: 'usage'; data: any }
  | { type: 'done'; data: { message_id: number; thread_id: string; content: string } }
  | { type: 'error'; data: { message: string } };

// API Client Class
class APIClient {
  private baseURL: string;
  private apiKey?: string;

  constructor(baseURL: string = API_BASE_URL, apiKey?: string) {
    this.baseURL = baseURL;
    this.apiKey = apiKey;
  }

  private getHeaders(): HeadersInit {
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
    };

    if (this.apiKey) {
      headers['X-API-Key'] = this.apiKey;
    }

    return headers;
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseURL}${API_PREFIX}${endpoint}`;

    const response = await fetch(url, {
      ...options,
      headers: {
        ...this.getHeaders(),
        ...options.headers,
      },
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ message: response.statusText }));
      throw new Error(error.message || `HTTP ${response.status}`);
    }

    return response.json();
  }

  // Threads
  async createThread(data?: CreateThreadRequest): Promise<Thread> {
    return this.request<Thread>('/threads', {
      method: 'POST',
      body: JSON.stringify(data || {}),
    });
  }

  async getThread(threadId: string): Promise<Thread> {
    return this.request<Thread>(`/threads/${threadId}`);
  }

  async listThreads(limit: number = 50): Promise<{ threads: Thread[]; cursor: string | null }> {
    return this.request(`/threads?limit=${limit}`);
  }

  async deleteThread(threadId: string, hard: boolean = false): Promise<void> {
    await this.request(`/threads/${threadId}?hard=${hard}`, {
      method: 'DELETE',
    });
  }

  // Messages
  async listMessages(threadId: string, limit?: number): Promise<{ messages: Message[] }> {
    const params = limit ? `?limit=${limit}` : '';
    return this.request(`/threads/${threadId}/messages${params}`);
  }

  async sendMessage(
    threadId: string,
    data: SendMessageRequest
  ): Promise<SendMessageResponse> {
    return this.request<SendMessageResponse>(`/threads/${threadId}/messages`, {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  // Streaming
  async *streamChat(data: {
    thread_id?: string;
    agent: string;
    message: string;
    params?: Record<string, any>;
  }): AsyncGenerator<StreamEvent> {
    const url = `${this.baseURL}${API_PREFIX}/stream/chat`;

    console.log('Streaming to:', url, 'with data:', data);

    const response = await fetch(url, {
      method: 'POST',
      headers: this.getHeaders(),
      body: JSON.stringify(data),
    });

    if (!response.ok) {
      const errorText = await response.text();
      console.error('Stream error:', response.status, errorText);
      throw new Error(`HTTP ${response.status}: ${errorText}`);
    }

    const reader = response.body?.getReader();
    if (!reader) {
      throw new Error('No response body');
    }

    const decoder = new TextDecoder();
    let buffer = '';
    let currentEvent = '';

    while (true) {
      const { done, value } = await reader.read();

      if (done) break;

      buffer += decoder.decode(value, { stream: true });

      const lines = buffer.split('\n');
      buffer = lines.pop() || '';

      for (const line of lines) {
        if (!line.trim()) {
          // Empty line marks end of an event
          currentEvent = '';
          continue;
        }

        if (line.startsWith('event: ')) {
          currentEvent = line.substring(7).trim();
        } else if (line.startsWith('data: ')) {
          try {
            const eventData = JSON.parse(line.substring(6));
            if (currentEvent) {
              yield { type: currentEvent, data: eventData } as StreamEvent;
            }
          } catch (e) {
            console.error('Failed to parse SSE data:', line, e);
          }
        }
      }
    }
  }

  // Agents
  async listAgents(): Promise<{ agents: Agent[] }> {
    return this.request('/agents');
  }

  // Health
  async health(): Promise<{ status: string; version: string; timestamp: string }> {
    const response = await fetch(`${this.baseURL}/healthz`);
    return response.json();
  }
}

// Export singleton instance
export const apiClient = new APIClient();

// Export class for custom instances
export { APIClient };

