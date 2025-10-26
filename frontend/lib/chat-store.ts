import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';
import { apiClient } from './api-client';
import type { Thread } from './api-client';

interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  created_at?: string;
}

interface ThreadCache {
  thread: Thread;
  messages: ChatMessage[];
  lastFetched: number;
}

interface ChatStore {
  // Cached data
  threads: Thread[];
  threadCache: Map<string, ThreadCache>;
  currentThreadId: string | undefined;

  // Loading states
  isLoadingThreads: boolean;
  isLoadingMessages: boolean;
  isCreatingThread: boolean;

  // Actions
  setCurrentThread: (threadId: string | undefined) => void;
  loadThreads: (force?: boolean) => Promise<void>;
  loadMessages: (threadId: string, force?: boolean) => Promise<ChatMessage[]>;
  addMessage: (threadId: string, message: ChatMessage) => void;
  updateMessage: (threadId: string, messageId: string, content: string) => void;
  createThread: (title?: string) => Promise<Thread>;
  deleteThread: (threadId: string) => Promise<void>;
  clearCache: () => void;
  addThreadToList: (thread: Thread) => void;

  // Helper to get cached messages
  getCachedMessages: (threadId: string) => ChatMessage[] | undefined;
}

const CACHE_TTL = 5 * 60 * 1000; // 5 minutes

export const useChatStore = create<ChatStore>()(
  persist(
    (set, get) => ({
      // Initial state
      threads: [],
      threadCache: new Map(),
      currentThreadId: undefined,
      isLoadingThreads: false,
      isLoadingMessages: false,
      isCreatingThread: false,

      // Set current thread
      setCurrentThread: (threadId) => {
        set({ currentThreadId: threadId });
      },

      // Load threads from API
      loadThreads: async (force = false) => {
        const state = get();

        // Skip if already loading
        if (state.isLoadingThreads) return;

        // Check cache (if not forcing reload)
        if (!force && state.threads.length > 0) {
          return;
        }

        set({ isLoadingThreads: true });

        try {
          const data = await apiClient.listThreads(100);
          set({
            threads: data.threads,
            isLoadingThreads: false
          });
        } catch (error) {
          console.error('Failed to load threads:', error);
          set({ isLoadingThreads: false });
        }
      },

      // Load messages for a thread
      loadMessages: async (threadId, force = false) => {
        const state = get();
        const cached = state.threadCache.get(threadId);
        const now = Date.now();

        // Return cached if valid and not forcing
        if (!force && cached && (now - cached.lastFetched) < CACHE_TTL) {
          return cached.messages;
        }

        // Skip if already loading
        if (state.isLoadingMessages) {
          return cached?.messages || [];
        }

        set({ isLoadingMessages: true });

        try {
          const data = await apiClient.listMessages(threadId);
          const messages: ChatMessage[] = data.messages
            .filter(msg => msg.role === 'user' || msg.role === 'assistant')
            .map(msg => ({
              id: msg.id.toString(),
              role: msg.role as 'user' | 'assistant',
              content: msg.content,
              created_at: msg.created_at,
            }));

          // Update cache
          const newCache = new Map(state.threadCache);
          newCache.set(threadId, {
            thread: state.threads.find(t => t.id === threadId)!,
            messages,
            lastFetched: now,
          });

          set({
            threadCache: newCache,
            isLoadingMessages: false
          });

          return messages;
        } catch (error) {
          console.error('Failed to load messages:', error);
          set({ isLoadingMessages: false });
          return cached?.messages || [];
        }
      },

      // Add a new message to cache (optimistic update)
      addMessage: (threadId, message) => {
        const state = get();
        const cached = state.threadCache.get(threadId);
        const newCache = new Map(state.threadCache);

        if (cached) {
          // Thread exists in cache, add message
          newCache.set(threadId, {
            ...cached,
            messages: [...cached.messages, message],
            lastFetched: Date.now(),
          });
        } else {
          // Thread doesn't exist yet (new thread), create temporary cache entry
          const thread = state.threads.find(t => t.id === threadId);
          newCache.set(threadId, {
            thread: thread || {
              id: threadId,
              title: null,
              thread_metadata: {},
              created_at: new Date().toISOString(),
              updated_at: new Date().toISOString(),
              deleted_at: null,
            },
            messages: [message],
            lastFetched: Date.now(),
          });
        }

        set({ threadCache: newCache });
      },

      // Update a message in cache (for streaming)
      updateMessage: (threadId, messageId, content) => {
        const state = get();
        const cached = state.threadCache.get(threadId);

        if (cached) {
          const newCache = new Map(state.threadCache);
          newCache.set(threadId, {
            ...cached,
            messages: cached.messages.map(msg =>
              msg.id === messageId ? { ...msg, content } : msg
            ),
            lastFetched: Date.now(),
          });
          set({ threadCache: newCache });
        } else {
          // If cache doesn't exist yet, create it with the updated message
          const thread = state.threads.find(t => t.id === threadId);
          const newCache = new Map(state.threadCache);
          newCache.set(threadId, {
            thread: thread || {
              id: threadId,
              title: null,
              thread_metadata: {},
              created_at: new Date().toISOString(),
              updated_at: new Date().toISOString(),
              deleted_at: null,
            },
            messages: [{
              id: messageId,
              role: 'assistant',
              content: content,
            }],
            lastFetched: Date.now(),
          });
          set({ threadCache: newCache });
        }
      },

      // Create a new thread
      createThread: async (title) => {
        set({ isCreatingThread: true });

        try {
          const thread = await apiClient.createThread({ title });

          // Add to threads list at the top
          set(state => ({
            threads: [thread, ...state.threads],
            isCreatingThread: false,
          }));

          // Initialize empty cache for this thread
          const newCache = new Map(get().threadCache);
          newCache.set(thread.id, {
            thread,
            messages: [],
            lastFetched: Date.now(),
          });
          set({ threadCache: newCache });

          return thread;
        } catch (error) {
          console.error('Failed to create thread:', error);
          set({ isCreatingThread: false });
          throw error;
        }
      },

      // Add thread to list (for optimistic updates)
      addThreadToList: (thread) => {
        set(state => ({
          threads: [thread, ...state.threads],
        }));

        // Initialize cache entry
        const newCache = new Map(get().threadCache);
        newCache.set(thread.id, {
          thread,
          messages: [],
          lastFetched: Date.now(),
        });
        set({ threadCache: newCache });
      },

      // Delete a thread
      deleteThread: async (threadId) => {
        try {
          await apiClient.deleteThread(threadId);

          // Remove from cache
          const newCache = new Map(get().threadCache);
          newCache.delete(threadId);

          set(state => ({
            threads: state.threads.filter(t => t.id !== threadId),
            threadCache: newCache,
            currentThreadId: state.currentThreadId === threadId ? undefined : state.currentThreadId,
          }));
        } catch (error) {
          console.error('Failed to delete thread:', error);
          throw error;
        }
      },

      // Clear all cache
      clearCache: () => {
        set({
          threads: [],
          threadCache: new Map(),
          currentThreadId: undefined,
        });
      },

      // Get cached messages without fetching
      getCachedMessages: (threadId) => {
        const cached = get().threadCache.get(threadId);
        return cached?.messages;
      },
    }),
    {
      name: 'chat-storage',
      storage: createJSONStorage(() => localStorage),
      // Only persist threads list, not full cache
      partialize: (state) => ({
        threads: state.threads,
        currentThreadId: state.currentThreadId,
      }),
    }
  )
);

