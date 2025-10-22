/**
 * BGB Chat Hook - React Hook für Streaming Chat mit automatischer History vom Backend
 * Backend lädt History automatisch aus PostgreSQL - Frontend muss nur speichern!
 */
'use client';

import { useState, useCallback } from 'react';
import { streamChat, type ChatChunk } from '@/lib/api/bgb-chat-api';
import { saveMessage, saveToolResult } from '@/lib/actions/chat-actions';

interface ToolCall {
  id: string;
  name: string;
  arguments: Record<string, any>;
  status: string;
}

interface UseChatOptions {
  chatId: string;
  onChunkReceived?: (chunk: ChatChunk) => void;
  onComplete?: () => void;
  onError?: (error: Error) => void;
}

export function useBGBChat({ chatId, onChunkReceived, onComplete, onError }: UseChatOptions) {
  const [isLoading, setIsLoading] = useState(false);
  const [currentMessage, setCurrentMessage] = useState('');
  const [thinkingContent, setThinkingContent] = useState('');
  const [toolCalls, setToolCalls] = useState<ToolCall[]>([]);

  const sendMessage = useCallback(async (userMessage: string) => {
    setIsLoading(true);
    setCurrentMessage('');
    setThinkingContent('');
    setToolCalls([]);

    try {
      // 1. Speichere User Message in PostgreSQL
      await saveMessage(chatId, 'user', userMessage);

      // 2. Backend lädt History AUTOMATISCH aus PostgreSQL!
      //    Wir müssen KEINE History mitsenden!

      // 3. Stream Response vom Backend (Backend holt sich History selbst!)
      let assistantMessage = '';
      let assistantThinking = '';
      let currentToolCalls: ToolCall[] = [];
      let assistantMessageId: string | null = null;

      for await (const chunk of streamChat(chatId, userMessage)) {
        // Callback für UI Updates
        onChunkReceived?.(chunk);

        switch (chunk.type) {
          case 'thinking':
            if (chunk.thinking_content) {
              assistantThinking += chunk.thinking_content;
              setThinkingContent(assistantThinking);
            }
            break;

          case 'text':
            if (chunk.content) {
              assistantMessage += chunk.content;
              setCurrentMessage(assistantMessage);
            }
            break;

          case 'tool_call':
            if (chunk.tool_call) {
              currentToolCalls.push(chunk.tool_call);
              setToolCalls([...currentToolCalls]);
            }
            break;

          case 'tool_result':
            if (chunk.tool_result) {
              // Speichere Tool Result separat
              if (assistantMessageId) {
                await saveToolResult(
                  assistantMessageId,
                  chunk.tool_result.tool_call_id,
                  chunk.tool_result.metadata?.tool_name || 'unknown',
                  chunk.tool_result.output,
                  chunk.tool_result.metadata
                );
              }
            }
            break;

          case 'done':
            // 4. Speichere Assistant Response in PostgreSQL
            if (assistantMessage) {
              const savedMessage = await saveMessage(
                chatId,
                'assistant',
                assistantMessage,
                assistantThinking || undefined,
                currentToolCalls.length > 0 ? currentToolCalls : undefined
              );
              assistantMessageId = savedMessage.id;
            }
            break;

          case 'error':
            throw new Error(chunk.content || 'Unknown error');
        }
      }

      setIsLoading(false);
      onComplete?.();
    } catch (error) {
      console.error('Chat error:', error);
      setIsLoading(false);
      onError?.(error as Error);
    }
  }, [chatId, onChunkReceived, onComplete, onError]);

  return {
    sendMessage,
    isLoading,
    currentMessage,
    thinkingContent,
    toolCalls,
  };
}

