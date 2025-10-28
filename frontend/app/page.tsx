'use client';

import { useState } from 'react';
import { AppSidebar } from "@/components/app-sidebar"
import InputDemo from '@/components/chat-interface';
import {
  SidebarInset,
  SidebarProvider,
  SidebarTrigger,
} from "@/components/ui/sidebar"
import { useChatStore } from '@/lib/chat-store';

export default function Page() {
  const [selectedThreadId, setSelectedThreadId] = useState<string | undefined>();
  const { loadThreads } = useChatStore();

  const handleThreadSelect = (threadId: string) => {
    setSelectedThreadId(threadId);
  };

  const handleNewThread = () => {
    setSelectedThreadId(undefined);
  };

  const handleThreadCreated = (threadId: string) => {
    setSelectedThreadId(threadId);
    // Reload threads to show the new one in sidebar
    loadThreads(true);
  };

  return (
    <SidebarProvider>
      <AppSidebar
        selectedThreadId={selectedThreadId}
        onThreadSelect={handleThreadSelect}
        onNewThread={handleNewThread}
      />
      <SidebarInset className="flex flex-col h-screen overflow-hidden">
        <InputDemo
          key={selectedThreadId || 'new'}
          threadId={selectedThreadId}
          onThreadCreated={handleThreadCreated}
        />
      </SidebarInset>
    </SidebarProvider>
  )
}
