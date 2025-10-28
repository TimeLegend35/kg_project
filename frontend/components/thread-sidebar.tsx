'use client';

import { useState, useEffect } from 'react';
import { Plus, MessageSquare, Trash2, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Card } from '@/components/ui/card';
import { apiClient, Thread } from '@/lib/api-client';
import { cn } from '@/lib/utils';

interface ThreadSidebarProps {
  selectedThreadId?: string;
  onThreadSelect: (threadId: string) => void;
  onNewThread: () => void;
}

export function ThreadSidebar({ selectedThreadId, onThreadSelect, onNewThread }: ThreadSidebarProps) {
  const [threads, setThreads] = useState<Thread[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    loadThreads();
  }, []);

  const loadThreads = async () => {
    try {
      setIsLoading(true);
      const { threads: threadList } = await apiClient.listThreads(50);
      setThreads(threadList);
    } catch (err) {
      console.error('Failed to load threads:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleDelete = async (threadId: string, e: React.MouseEvent) => {
    e.stopPropagation();

    if (!confirm('Thread wirklich löschen?')) return;

    try {
      await apiClient.deleteThread(threadId, false);
      setThreads(prev => prev.filter(t => t.id !== threadId));

      if (selectedThreadId === threadId) {
        onNewThread();
      }
    } catch (err) {
      console.error('Failed to delete thread:', err);
    }
  };

  const handleNewThread = () => {
    onNewThread();
    loadThreads(); // Refresh list
  };

  const addThread = (thread: Thread) => {
    setThreads(prev => [thread, ...prev]);
  };

  return (
    <div className="flex flex-col h-full border-r bg-muted/10">
      {/* Header */}
      <div className="p-4 border-b">
        <Button onClick={handleNewThread} className="w-full" size="sm">
          <Plus className="h-4 w-4 mr-2" />
          Neuer Chat
        </Button>
      </div>

      {/* Thread List */}
      <ScrollArea className="flex-1">
        {isLoading ? (
          <div className="flex items-center justify-center p-8">
            <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
          </div>
        ) : threads.length === 0 ? (
          <div className="p-4 text-center text-sm text-muted-foreground">
            Keine Threads vorhanden
          </div>
        ) : (
          <div className="p-2 space-y-1">
            {threads.map((thread) => (
              <Card
                key={thread.id}
                className={cn(
                  'p-3 cursor-pointer hover:bg-accent transition-colors',
                  selectedThreadId === thread.id && 'bg-accent'
                )}
                onClick={() => onThreadSelect(thread.id)}
              >
                <div className="flex items-start justify-between gap-2">
                  <div className="flex items-start gap-2 flex-1 min-w-0">
                    <MessageSquare className="h-4 w-4 mt-0.5 flex-shrink-0 text-muted-foreground" />
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium truncate">
                        {thread.title || 'Unbenannter Chat'}
                      </p>
                      <p className="text-xs text-muted-foreground">
                        {new Date(thread.updated_at).toLocaleDateString('de-DE', {
                          day: '2-digit',
                          month: '2-digit',
                          year: '2-digit',
                          hour: '2-digit',
                          minute: '2-digit',
                        })}
                      </p>
                    </div>
                  </div>
                  <Button
                    variant="ghost"
                    size="icon"
                    className="h-6 w-6 flex-shrink-0"
                    onClick={(e) => handleDelete(thread.id, e)}
                  >
                    <Trash2 className="h-3 w-3" />
                  </Button>
                </div>
              </Card>
            ))}
          </div>
        )}
      </ScrollArea>
    </div>
  );
}

