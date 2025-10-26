'use server';

import { revalidatePath } from 'next/cache';

/**
 * Server Actions für BGB Chat API
 * Diese werden auf dem Next.js Server ausgeführt
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8080';
const API_PREFIX = '/api/v1';

// Types
export interface Thread {
  id: string;
  title: string | null;
  thread_metadata: Record<string, any>;
  created_at: string;
  updated_at: string;
  deleted_at: string | null;
}

export interface ToolCall {
  name: string;
  arguments: string | Record<string, any>;
  result?: string;
}

export interface Usage {
  prompt_tokens?: number;
  completion_tokens?: number;
  total_tokens?: number;
  input_tokens?: number;
  output_tokens?: number;
}

export interface Message {
  id: number;
  thread_id: string;
  role: 'user' | 'assistant' | 'tool';
  content: string;
  agent_name: string | null;
  tool_calls: ToolCall[] | null;
  usage: Usage | null;
  created_at: string;
}

export interface Agent {
  name: string;
  description: string;
  available: boolean;
}

// Helper function
async function apiRequest<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${API_BASE_URL}${API_PREFIX}${endpoint}`;

  const response = await fetch(url, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
    cache: 'no-store', // Wichtig für Server Actions
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({
      message: response.statusText
    }));
    throw new Error(error.message || `HTTP ${response.status}`);
  }

  return response.json();
}

/**
 * Thread Actions
 */

export async function getThreads(limit: number = 50) {
  try {
    const data = await apiRequest<{ threads: Thread[]; cursor: string | null }>(
      `/threads?limit=${limit}`
    );
    return { success: true, data };
  } catch (error) {
    console.error('getThreads error:', error);
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Failed to fetch threads'
    };
  }
}

export async function createThread(data?: {
  title?: string;
  thread_metadata?: Record<string, any>
}) {
  try {
    const thread = await apiRequest<Thread>('/threads', {
      method: 'POST',
      body: JSON.stringify(data || {}),
    });

    revalidatePath('/');
    return { success: true, data: thread };
  } catch (error) {
    console.error('createThread error:', error);
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Failed to create thread'
    };
  }
}

export async function deleteThread(threadId: string, hard: boolean = false) {
  try {
    await apiRequest(`/threads/${threadId}?hard=${hard}`, {
      method: 'DELETE',
    });

    revalidatePath('/');
    return { success: true };
  } catch (error) {
    console.error('deleteThread error:', error);
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Failed to delete thread'
    };
  }
}

export async function getThread(threadId: string) {
  try {
    const thread = await apiRequest<Thread>(`/threads/${threadId}`);
    return { success: true, data: thread };
  } catch (error) {
    console.error('getThread error:', error);
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Failed to fetch thread'
    };
  }
}

/**
 * Message Actions
 */

export async function getMessages(threadId: string, limit?: number) {
  try {
    const params = limit ? `?limit=${limit}` : '';
    const data = await apiRequest<{ messages: Message[] }>(
      `/threads/${threadId}/messages${params}`
    );
    return { success: true, data };
  } catch (error) {
    console.error('getMessages error:', error);
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Failed to fetch messages'
    };
  }
}

export async function sendMessage(
  threadId: string,
  data: {
    agent: string;
    input: string;
    params?: Record<string, any>;
    stream?: boolean;
  }
) {
  try {
    const response = await apiRequest<{
      message: Message;
      usage?: any;
      tool_calls?: any[];
      meta?: Record<string, any>;
    }>(`/threads/${threadId}/messages`, {
      method: 'POST',
      body: JSON.stringify(data),
    });

    revalidatePath('/');
    return { success: true, data: response };
  } catch (error) {
    console.error('sendMessage error:', error);
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Failed to send message'
    };
  }
}

/**
 * Agent Actions
 */

export async function getAgents() {
  try {
    const data = await apiRequest<{ agents: Agent[] }>('/agents');
    return { success: true, data };
  } catch (error) {
    console.error('getAgents error:', error);
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Failed to fetch agents'
    };
  }
}

/**
 * Health Check Action
 */

export async function checkHealth() {
  try {
    const response = await fetch(`${API_BASE_URL}/healthz`, {
      cache: 'no-store',
    });
    const data = await response.json();
    return { success: true, data };
  } catch (error) {
    console.error('checkHealth error:', error);
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Failed to check health'
    };
  }
}

/**
 * Streaming Chat Action (Client-side fetch, da SSE)
 * Diese Funktion gibt die URL zurück, die der Client für SSE nutzen kann
 */

export async function getStreamChatUrl() {
  return `${API_BASE_URL}${API_PREFIX}/stream/chat`;
}

