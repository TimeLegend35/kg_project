/**
 * Chat API Route - Simplified für FastAPI Backend
 * Entfernt Vercel AI SDK, nutzt direkt unser LangGraph Backend
 */
import { auth } from "@/app/(auth)/auth";
import { streamChat } from "@/lib/api/bgb-chat-api";
import { saveMessages, getChatById, saveChat } from "@/lib/db/queries";
import { generateTitleWithBackend } from "@/lib/ai/bgb-provider";
import { ChatSDKError } from "@/lib/errors";

export const maxDuration = 60;

interface PostRequestBody {
  id: string;
  message: {
    role: string;
    content: string;
  };
  modelId?: string;
}

export async function POST(request: Request) {
  // Auth Check
  const session = await auth();
  if (!session?.user?.id) {
    return new ChatSDKError("unauthorized").toResponse();
  }

  // Parse Request
  let requestBody: PostRequestBody;
  try {
    requestBody = await request.json();
  } catch {
    return new ChatSDKError("bad_request:api").toResponse();
  }

  const { id: chatId, message } = requestBody;
  const userMessage = typeof message.content === 'string'
    ? message.content
    : JSON.stringify(message.content);

  try {
    // Prüfe ob Chat existiert, wenn nicht erstelle neuen
    const existingChat = await getChatById({ id: chatId });

    if (!existingChat) {
      // Erstelle neuen Chat
      await saveChat({
        id: chatId,
        userId: session.user.id,
        title: 'Neue Unterhaltung', // Wird später aktualisiert
      });
    }

    // Speichere User Message in DB
    await saveMessages({
      messages: [{
        id: crypto.randomUUID(),
        chatId,
        role: 'user',
        content: userMessage,
        createdAt: new Date(),
      }],
    });

    // Erstelle Response Stream für Frontend
    const encoder = new TextEncoder();
    const stream = new ReadableStream({
      async start(controller) {
        try {
          let assistantMessage = '';
          let hasToolCalls = false;

          // Stream von unserem FastAPI Backend
          for await (const chunk of streamChat(chatId, userMessage)) {
            // Sende Chunk zum Frontend im AI SDK Format
            const aiSDKChunk = convertToAISDKFormat(chunk);
            controller.enqueue(encoder.encode(`0:${JSON.stringify(aiSDKChunk)}\n`));

            // Sammle Assistant Message für DB-Speicherung
            if (chunk.type === 'text' && chunk.content) {
              assistantMessage += chunk.content;
            }

            if (chunk.type === 'tool_call') {
              hasToolCalls = true;
            }

            // Bei Done: Speichere Assistant Message und generiere Titel
            if (chunk.type === 'done') {
              // Speichere Assistant Response
              if (assistantMessage) {
                await saveMessages({
                  messages: [{
                    id: crypto.randomUUID(),
                    chatId,
                    role: 'assistant',
                    content: assistantMessage,
                    createdAt: new Date(),
                  }],
                });
              }

              // Generiere Titel für neue Chats
              if (!existingChat) {
                const title = await generateTitleWithBackend(chatId, userMessage);
                // Titel wird über separaten API Call aktualisiert
              }
            }
          }

          controller.close();
        } catch (error) {
          console.error('Stream error:', error);
          controller.error(error);
        }
      },
    });

    return new Response(stream, {
      headers: {
        'Content-Type': 'text/plain; charset=utf-8',
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive',
      },
    });

  } catch (error) {
    console.error('Chat error:', error);
    return new ChatSDKError("internal_server_error").toResponse();
  }
}

/**
 * Konvertiert unser Backend-Chunk-Format zu AI SDK Format
 */
function convertToAISDKFormat(chunk: any) {
  switch (chunk.type) {
    case 'text':
      return {
        type: 'text-delta',
        textDelta: chunk.content,
      };

    case 'thinking':
      return {
        type: 'text-delta',
        textDelta: `💭 ${chunk.thinking_content}\n`,
      };

    case 'tool_call':
      return {
        type: 'tool-call',
        toolCallId: chunk.tool_call?.id,
        toolName: chunk.tool_call?.name,
        args: chunk.tool_call?.arguments,
      };

    case 'tool_result':
      return {
        type: 'tool-result',
        toolCallId: chunk.tool_result?.tool_call_id,
        toolName: chunk.tool_result?.metadata?.tool_name,
        result: chunk.tool_result?.output,
      };

    case 'done':
      return {
        type: 'finish',
        finishReason: 'stop',
      };

    case 'error':
      return {
        type: 'error',
        error: chunk.content,
      };

    default:
      return chunk;
  }
}

