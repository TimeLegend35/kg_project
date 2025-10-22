/**
 * Custom Language Model Provider für FastAPI + LangGraph Backend
 * Ersetzt Vercel AI SDK Provider mit direkten Backend-Calls
 */

import { LanguageModelV1 } from '@ai-sdk/provider';
import { streamChat } from '@/lib/api/bgb-chat-api';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

/**
 * Custom Language Model das unser FastAPI Backend nutzt
 */
class BGBLanguageModel implements LanguageModelV1 {
  readonly specificationVersion = 'v1' as const;
  readonly provider = 'bgb-fastapi' as const;
  readonly modelId = 'qwen3:14B' as const;
  readonly defaultObjectGenerationMode = 'json' as const;

  async doGenerate(options: any): Promise<any> {
    // Nicht verwendet - wir nutzen nur doStream
    throw new Error('doGenerate not implemented - use streaming only');
  }

  async doStream(options: any): Promise<any> {
    const { prompt, chatId } = options;

    // Extrahiere die letzte User-Message aus dem Prompt
    const messages = prompt.messages || [];
    const lastMessage = messages[messages.length - 1];
    const userMessage = typeof lastMessage === 'string'
      ? lastMessage
      : lastMessage?.content || '';

    // Stream von unserem FastAPI Backend
    const stream = streamChat(chatId || 'default', userMessage);

    // Konvertiere unser Stream-Format zu AI SDK Format
    return {
      stream: this.convertToAISDKStream(stream),
      rawCall: { rawPrompt: prompt, rawSettings: {} },
    };
  }

  private async* convertToAISDKStream(backendStream: AsyncGenerator<any>) {
    for await (const chunk of backendStream) {
      switch (chunk.type) {
        case 'text':
          yield {
            type: 'text-delta',
            textDelta: chunk.content,
          };
          break;

        case 'thinking':
          yield {
            type: 'text-delta',
            textDelta: `[Thinking: ${chunk.thinking_content}]\n`,
          };
          break;

        case 'tool_call':
          yield {
            type: 'tool-call',
            toolCallType: 'function',
            toolCallId: chunk.tool_call?.id,
            toolName: chunk.tool_call?.name,
            args: chunk.tool_call?.arguments,
          };
          break;

        case 'tool_result':
          yield {
            type: 'tool-result',
            toolCallId: chunk.tool_result?.tool_call_id,
            result: chunk.tool_result?.output,
          };
          break;

        case 'done':
          yield {
            type: 'finish',
            finishReason: 'stop',
          };
          break;

        case 'error':
          yield {
            type: 'error',
            error: chunk.content,
          };
          break;
      }
    }
  }
}

/**
 * Custom Provider für alle Model-Typen
 */
export const bgbProvider = {
  languageModel: (modelId: string) => new BGBLanguageModel(),

  // Für Title Generation nutzen wir das gleiche Backend
  chat: (modelId: string) => new BGBLanguageModel(),
};

/**
 * Vereinfachter Provider Export
 * Alle Models nutzen unser FastAPI Backend
 */
export const myProvider = {
  languageModel: (modelId: string) => {
    // Ignoriere modelId - wir nutzen immer unser Backend
    return new BGBLanguageModel();
  },
};

/**
 * Helper für Title Generation mit unserem Backend
 */
export async function generateTitleWithBackend(chatId: string, firstMessage: string): Promise<string> {
  try {
    // Nutze das gleiche Backend für Title Generation
    // Einfacher Prompt für Titel
    const titlePrompt = `Erstelle einen kurzen, prägnanten Titel (max 6 Wörter) für ein Gespräch, das mit dieser Frage beginnt: "${firstMessage}". Antworte NUR mit dem Titel, ohne Anführungszeichen.`;

    let title = '';
    for await (const chunk of streamChat(chatId, titlePrompt)) {
      if (chunk.type === 'text' && chunk.content) {
        title += chunk.content;
      }
    }

    return title.trim() || 'Neue Unterhaltung';
  } catch (error) {
    console.error('Title generation failed:', error);
    return 'Neue Unterhaltung';
  }
}

