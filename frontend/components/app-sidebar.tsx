"use client"

import * as React from "react"
import {
    MessageSquare,
    Plus,
    Trash2,
    Loader2,
    Bot,
    Sparkles, Wrench, Space,
} from "lucide-react"

import {
    Sidebar,
    SidebarContent,
    SidebarFooter,
    SidebarHeader,
    SidebarRail,
    SidebarGroup,
    SidebarGroupContent,
    SidebarGroupLabel,
    SidebarMenu,
    SidebarMenuItem,
    useSidebar,
    SidebarMenuButton, SidebarTrigger,
} from "@/components/ui/sidebar"
import { Button } from "@/components/ui/button"
import { ScrollArea } from "@/components/ui/scroll-area"
import { useChatStore } from "@/lib/chat-store"
import { cn } from "@/lib/utils"

interface AppSidebarProps extends React.ComponentProps<typeof Sidebar> {
  selectedThreadId?: string;
  onThreadSelect: (threadId: string) => void;
  onNewThread: () => void;
}

export function AppSidebar({
  selectedThreadId,
  onThreadSelect,
  onNewThread,
  ...props
}: AppSidebarProps) {
  const { threads, isLoadingThreads, isCreatingThread, loadThreads, deleteThread } = useChatStore();

  React.useEffect(() => {
    // Load threads on mount, will use cache if available
    loadThreads();
  }, [loadThreads]);

  const handleDelete = async (threadId: string, e: React.MouseEvent) => {
    e.stopPropagation();

    if (!confirm('Thread wirklich löschen?')) return;

    try {
      await deleteThread(threadId);

      if (selectedThreadId === threadId) {
        onNewThread();
      }
    } catch (err) {
      console.error('Failed to delete thread:', err);
    }
  };

  const handleNewThread = () => {
    onNewThread();
  };
  const { toggleSidebar } = useSidebar()
  return (
    <Sidebar collapsible="icon" {...props}>
      <SidebarHeader>
        <SidebarMenu>
          <SidebarMenuItem>
            <div className="flex items-center gap-2">
              <SidebarMenuButton
                size="lg"
                className="w-full"
                onClick={toggleSidebar}
              >
                <div className="flex aspect-square size-8 items-center justify-center rounded-lg bg-primary text-primary-foreground">
                  <Space className="h-4 w-4" />
                </div>
                <div className="grid flex-1 text-left text-sm leading-tight">
                  <span className="truncate font-semibold">BGB AI Chat</span>
                  <span className="truncate text-xs">Rechtsassistent</span>
                </div>
              </SidebarMenuButton>
            </div>
          </SidebarMenuItem>
        </SidebarMenu>

      </SidebarHeader>

      <SidebarContent>
        <SidebarGroup>
          {/* Neuer Chat Button - über dem Label */}
          <div className="">
            <SidebarMenuButton
              size="lg"
              className="w-full"
              onClick={handleNewThread}
              disabled={isCreatingThread}
            >
              <div className="flex aspect-square size-8 items-center justify-center rounded-lg bg-primary text-primary-foreground">
                {isCreatingThread ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <Plus className="h-4 w-4" />
                )}
              </div>
              <div className="grid flex-1 text-left text-sm leading-tight">
                <span className="truncate font-semibold">
                  {isCreatingThread ? 'Wird erstellt...' : 'Neuer Chat'}
                </span>
              </div>
            </SidebarMenuButton>
          </div>

          <SidebarGroupLabel>Chat-Threads</SidebarGroupLabel>
          <SidebarGroupContent>

            {/* Chat-Liste - nur sichtbar wenn Sidebar nicht collapsed ist */}
            <div className="group-data-[collapsible=icon]:hidden">
              {isLoadingThreads ? (
                <div className="flex items-center justify-center p-8">
                  <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
                </div>
              ) : threads.length === 0 ? (
                <div className="p-4 text-center text-sm text-muted-foreground">
                  Keine Threads vorhanden
                </div>
              ) : (
                <ScrollArea className="h-[calc(100vh-200px)] mt-2">
                  <div className="space-y-1 px-2">
                    {threads.map((thread) => (
                      <div
                        key={thread.id}
                        onClick={() => onThreadSelect(thread.id)}
                        className={cn(
                          "relative group rounded-md w-56 py-2 px-2 text-sm cursor-pointer transition-colors",
                          "hover:bg-blue-100 dark:hover:bg-blue-900/30",
                          selectedThreadId === thread.id && "bg-blue-100 dark:bg-blue-900/40"
                        )}
                      >
                        <div className="flex items-center justify-between gap-2">
                          <p className="font-medium truncate text-left flex-1">
                            {thread.title || 'Unbenannter Chat'}
                          </p>
                        </div>
                      </div>
                    ))}
                  </div>
                </ScrollArea>
              )}
            </div>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>

      <SidebarFooter>
        <SidebarMenu>
          <SidebarMenuItem>
            <SidebarMenuButton size="sm">
              <span className="text-xs text-muted-foreground">
                v1.0.0 - BGB Assistant
              </span>
            </SidebarMenuButton>
          </SidebarMenuItem>
        </SidebarMenu>
      </SidebarFooter>
      <SidebarRail />
    </Sidebar>
  );
}
