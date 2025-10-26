'use client';

import { useRef, useState, useEffect } from 'react';
import { GlobeIcon } from 'lucide-react';

import {
  PromptInput,
  PromptInputActionAddAttachments,
  PromptInputActionMenu,
  PromptInputActionMenuContent,
  PromptInputActionMenuTrigger,
  PromptInputAttachment,
  PromptInputAttachments,
  PromptInputBody,
  PromptInputButton,
  type PromptInputMessage,
  PromptInputModelSelect,
  PromptInputModelSelectContent,
  PromptInputModelSelectItem,
  PromptInputModelSelectTrigger,
  PromptInputModelSelectValue,
  PromptInputSpeechButton,
  PromptInputSubmit,
  PromptInputTextarea,
  PromptInputFooter,
  PromptInputTools,
} from '@/components/ai-elements/prompt-input';

import { Conversation, ConversationContent, ConversationScrollButton } from '@/components/ai-elements/conversation';
import { Message, MessageContent } from '@/components/ai-elements/message';
import { Response } from '@/components/ai-elements/response';
import { Tool, ToolHeader, ToolContent, ToolInput, ToolOutput } from '@/components/ai-elements/tool';

import { apiClient } from '@/lib/api-client';
import { useChatStore, type ToolCall } from '@/lib/chat-store';

const models = [
  { id: 'qwen', name: 'Qwen' },
  { id: 'gemini', name: 'Gemini' },
];

interface InputDemoProps {
  threadId?: string;
  onThreadCreated?: (threadId: string) => void;
}

const InputDemo = ({ threadId: initialThreadId, onThreadCreated }: InputDemoProps) => {
  const [text, setText] = useState<string>('');
  const [model, setModel] = useState<string>(models[0].id);
  const [useWebSearch, setUseWebSearch] = useState<boolean>(false);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [threadId, setThreadId] = useState<string | undefined>(initialThreadId);
  const [isStreaming, setIsStreaming] = useState<boolean>(false);
  const [isThinking, setIsThinking] = useState<boolean>(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const { getCachedMessages, loadMessages, addMessage, updateMessage, addToolCall, updateToolCall, addThreadToList } = useChatStore();

  // Get messages from cache
  const cachedMessages = threadId ? getCachedMessages(threadId) : undefined;

  // Load messages when threadId changes (but not during streaming)
  useEffect(() => {
    if (isStreaming) {
      return;
    }

    if (initialThreadId) {
      setThreadId(initialThreadId);
      loadMessages(initialThreadId);
    } else if (!initialThreadId) {
      setThreadId(undefined);
    }
  }, [initialThreadId, isStreaming, loadMessages]);

  const handleSubmit = async (message: PromptInputMessage) => {
    const hasText = Boolean(message.text);
    const hasAttachments = Boolean(message.files?.length);

    if (!(hasText || hasAttachments)) {
      return;
    }

    const userMessage = message.text || 'Sent with attachments';

    setText('');
    setIsLoading(true);
    setIsStreaming(true);
    setIsThinking(true);

    const userMsg = {
      id: Date.now().toString(),
      role: 'user' as const,
      content: userMessage,
    };

    const assistantMsgId = (Date.now() + 1).toString();
    const assistantMsg = {
      id: assistantMsgId,
      role: 'assistant' as const,
      content: '',
      toolCalls: [],
    };

    let workingThreadId = threadId || `temp-${Date.now()}`;

    addMessage(workingThreadId, userMsg);
    addMessage(workingThreadId, assistantMsg);

    try {
      const stream = apiClient.streamChat({
        thread_id: threadId,
        agent: model,
        message: userMessage,
        params: {
          webSearch: useWebSearch,
        },
      });

      let actualThreadId = threadId;
      let toolCallCount = 0;

      for await (const event of stream) {
        console.log('Stream event:', event);

        switch (event.type) {
          case 'start':
            setIsThinking(true);
            break;

          case 'thinking':
            // Backend sendet thinking status
            if (event.data.status === 'processing') {
              setIsThinking(true);
            } else if (event.data.status === 'done') {
              setIsThinking(false);
            }
            break;

          case 'metadata':
            const newThreadId = event.data.thread_id;
            actualThreadId = newThreadId;
            setThreadId(newThreadId);

            if (!threadId) {
              addThreadToList({
                id: newThreadId,
                title: userMessage.substring(0, 50) + (userMessage.length > 50 ? '...' : ''),
                thread_metadata: {},
                created_at: new Date().toISOString(),
                updated_at: new Date().toISOString(),
                deleted_at: null,
              });
            }

            if (workingThreadId !== newThreadId && workingThreadId.startsWith('temp-')) {
              const tempMessages = getCachedMessages(workingThreadId);
              if (tempMessages) {
                tempMessages.forEach(msg => addMessage(newThreadId, msg));
              }
              workingThreadId = newThreadId;
            } else if (!threadId) {
              workingThreadId = newThreadId;
            }

            if (onThreadCreated && !threadId) {
              onThreadCreated(newThreadId);
            }
            break;

          case 'tool_call':
            // Tool wird dauerhaft in der Nachricht gespeichert
            const toolCall: ToolCall = {
              name: event.data.name || 'Tool',
              arguments: event.data.arguments || event.data.args,
              result: event.data.result,
              state: event.data.result ? 'finished' : 'input-available',
            };
            if (workingThreadId) {
              addToolCall(workingThreadId, assistantMsgId, toolCall);
              toolCallCount++;
            }
            break;

          case 'token':
            // Erste token bedeutet thinking ist vorbei
            setIsThinking(false);
            if (workingThreadId) {
              const currentMsg = getCachedMessages(workingThreadId)?.find(m => m.id === assistantMsgId);
              const newContent = (currentMsg?.content || '') + event.data.token;
              updateMessage(workingThreadId, assistantMsgId, newContent);
            }
            break;

          case 'done':
            console.log('Message completed:', event.data);
            setIsThinking(false);

            // Setze alle Tool-Calls auf "finished"
            if (workingThreadId && toolCallCount > 0) {
              const currentMsg = getCachedMessages(workingThreadId)?.find(m => m.id === assistantMsgId);
              if (currentMsg?.toolCalls) {
                currentMsg.toolCalls.forEach((_, idx) => {
                  updateToolCall(workingThreadId, assistantMsgId, idx, { state: 'finished' });
                });
              }
            }
            break;

          case 'error':
            console.error('Stream error:', event.data.message);
            if (workingThreadId) {
              updateMessage(workingThreadId, assistantMsgId, `Error: ${event.data.message}`);
            }
            setIsThinking(false);
            break;
        }
      }
    } catch (error) {
      console.error('Failed to send message:', error);
      const errorMsg = {
        id: Date.now().toString(),
        role: 'assistant' as const,
        content: `Error: ${error instanceof Error ? error.message : 'Failed to send message'}`,
      };
      addMessage(workingThreadId, errorMsg);
    } finally {
      setIsLoading(false);
      setIsStreaming(false);
      setIsThinking(false);
    }
  };

  return (
    <div className="flex flex-col h-screen w-full">
      <div className="flex-1 overflow-hidden flex justify-center">
        <div className="max-w-7xl w-7/8 h-full">
          <Conversation className="h-full">
            <ConversationContent>
              {(!cachedMessages || cachedMessages.length === 0) && !isLoading ? (
                <div className="flex flex-col items-center justify-center h-full gap-4 text-center p-8">
                  <div className="flex items-center justify-center w-16 h-16 rounded-full bg-primary/10">
                    <svg
                      className="w-8 h-8 text-primary"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z"
                      />
                    </svg>
                  </div>
                  <div className="space-y-2">
                    <h3 className="text-xl font-semibold">Neuer Chat gestartet</h3>
                    <p className="text-sm text-muted-foreground max-w-sm">
                      Stellen Sie Ihre Frage zum BGB. Der Assistent hilft Ihnen gerne weiter.
                    </p>
                  </div>
                </div>
              ) : (
                <>
                  {(cachedMessages || []).map((message) => (
                    <Message from={message.role} key={message.id}>
                      <MessageContent>
                        {/* Chain of Thought - Tool Calls als aufklappbare Komponenten */}
                        {message.toolCalls && message.toolCalls.length > 0 && (
                          <div className="space-y-2 mb-4">
                            <div className="text-xs text-muted-foreground font-medium mb-2">
                              Chain of Thought
                            </div>
                            {message.toolCalls.map((toolCall, idx) => (
                              <Tool key={idx} defaultOpen={false}>
                                <ToolHeader
                                  title={toolCall.name}
                                  type="tool-call"
                                  state={toolCall.state}
                                />
                                <ToolContent>
                                  <ToolInput input={toolCall.arguments} />
                                  {toolCall.result && (
                                    <ToolOutput output={toolCall.result} errorText={undefined} />
                                  )}
                                </ToolContent>
                              </Tool>
                            ))}
                          </div>
                        )}

                        {/* Thinking Indicator während des Streamings */}
                        {message.role === 'assistant' && isThinking && message.id === (cachedMessages?.[cachedMessages.length - 1]?.id) && (
                          <div className="flex items-center gap-2 text-muted-foreground mb-3">
                            <div className="flex space-x-1">
                              <div className="w-2 h-2 bg-primary rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
                              <div className="w-2 h-2 bg-primary rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
                              <div className="w-2 h-2 bg-primary rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
                            </div>
                            <span className="text-sm italic">Thinking...</span>
                          </div>
                        )}

                        {/* Antwort-Text */}
                        {message.content && (
                          <Response>
                            {message.content}
                          </Response>
                        )}
                      </MessageContent>
                    </Message>
                  ))}
                </>
              )}
            </ConversationContent>
            <ConversationScrollButton />
          </Conversation>
        </div>
      </div>

      <div className="sticky bottom-0 bg-background p-4">
        <div className="max-w-7xl mx-auto w-7/8">
          <PromptInput onSubmit={handleSubmit} globalDrop multiple>
            <PromptInputBody>
              <PromptInputAttachments>
                {(attachment) => <PromptInputAttachment data={attachment} />}
              </PromptInputAttachments>
              <PromptInputTextarea
                onChange={(e) => setText(e.target.value)}
                ref={textareaRef}
                value={text}
                placeholder="Nachricht eingeben..."
              />
            </PromptInputBody>
            <PromptInputFooter>
              <PromptInputTools>
                <PromptInputActionMenu>
                  <PromptInputActionMenuTrigger />
                  <PromptInputActionMenuContent>
                    <PromptInputActionAddAttachments />
                  </PromptInputActionMenuContent>
                </PromptInputActionMenu>
                <PromptInputSpeechButton
                  onTranscriptionChange={setText}
                  textareaRef={textareaRef}
                />
                <PromptInputButton
                  onClick={() => setUseWebSearch(!useWebSearch)}
                  variant={useWebSearch ? 'default' : 'ghost'}
                >
                  <GlobeIcon size={16} />
                  <span>Search</span>
                </PromptInputButton>
                <PromptInputModelSelect
                  onValueChange={(value) => {
                    setModel(value);
                  }}
                  value={model}
                >
                  <PromptInputModelSelectTrigger>
                    <PromptInputModelSelectValue />
                  </PromptInputModelSelectTrigger>
                  <PromptInputModelSelectContent>
                    {models.map((model) => (
                      <PromptInputModelSelectItem key={model.id} value={model.id}>
                        {model.name}
                      </PromptInputModelSelectItem>
                    ))}
                  </PromptInputModelSelectContent>
                </PromptInputModelSelect>
              </PromptInputTools>
              <PromptInputSubmit
                disabled={!text || isLoading}
              />
            </PromptInputFooter>
          </PromptInput>
        </div>
      </div>
    </div>
  );
};

export { InputDemo };
export default InputDemo;

