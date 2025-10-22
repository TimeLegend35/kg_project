/**
 * BGB Chat API Provider
 * Custom provider für die Integration mit unserem FastAPI Backend
 */

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';


export interface ToolCall {
  id: string;
  name: string;
  arguments: Record<string, any>;
  status: 'pending' | 'running' | 'completed' | 'failed';
}

export interface ChatChunk {
  type: 'text' | 'tool_call' | 'tool_result' | 'thinking' | 'done' | 'error';
  content?: string;
  tool_call?: ToolCall;
  tool_result?: {
    tool_call_id: string;
    output: string;
    metadata?: Record<string, any>;
  };
  thinking_content?: string;
  metadata?: Record<string, any>;
}


/**
 * Stream chat responses with Server-Sent Events
 * Backend lädt History automatisch aus PostgreSQL!
 */
export async function* streamChat(
  chatId: string,
  message: string
): AsyncGenerator<ChatChunk> {
  const response = await fetch(`${API_URL}/chat/stream`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      chat_id: chatId,
      message,
      stream: true,
    }),
  });

  if (!response.ok) {
    throw new Error(`Failed to stream chat: ${response.statusText}`);
  }

  const reader = response.body?.getReader();
  const decoder = new TextDecoder();

  if (!reader) {
    throw new Error('No response body');
  }

  try {
    while (true) {
      const { done, value } = await reader.read();

      if (done) break;

      const chunk = decoder.decode(value);
      const lines = chunk.split('\n');

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const data = line.slice(6);

          if (data.trim()) {
            try {
              const parsed: ChatChunk = JSON.parse(data);
              yield parsed;

              if (parsed.type === 'done') {
                return;
              }
            } catch (e) {
              console.error('Failed to parse SSE data:', e);
            }
          }
        }
      }
    }
  } finally {
    reader.releaseLock();
  }
}

/**
 * Health check
 */
export async function healthCheck(): Promise<{ status: string; version: string }> {
  const response = await fetch(`${API_URL}/health`);

  if (!response.ok) {
    throw new Error(`Health check failed: ${response.statusText}`);
  }

  return response.json();
}

/**
 * Detailed health check
 */
export async function detailedHealthCheck(): Promise<Record<string, any>> {
  const response = await fetch(`${API_URL}/health/detailed`);

  if (!response.ok) {
    throw new Error(`Health check failed: ${response.statusText}`);
  }

  return response.json();
}

