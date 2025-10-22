/**
 * BGB Chat Actions - Server Actions für Chat History Management
 * Nutzt Drizzle ORM für PostgreSQL Persistence
 */
'use server';

import { db } from '@/lib/db';
import { chats, messages, toolResults, type Chat, type Message } from '@/lib/db/schema-bgb';
import { eq, desc } from 'drizzle-orm';
import { revalidatePath } from 'next/cache';

/**
 * Create a new chat
 */
export async function createChat(userId: string = 'default_user', title: string = 'Neue Unterhaltung'): Promise<Chat> {
  const [chat] = await db.insert(chats).values({
    userId,
    title,
  }).returning();

  revalidatePath('/');
  return chat;
}

/**
 * Get all chats for a user
 */
export async function getChats(userId: string = 'default_user'): Promise<Chat[]> {
  return await db
    .select()
    .from(chats)
    .where(eq(chats.userId, userId))
    .orderBy(desc(chats.updatedAt));
}

/**
 * Get a specific chat with messages
 */
export async function getChat(chatId: string): Promise<{ chat: Chat; messages: Message[] } | null> {
  const [chat] = await db.select().from(chats).where(eq(chats.id, chatId));

  if (!chat) return null;

  const chatMessages = await db
    .select()
    .from(messages)
    .where(eq(messages.chatId, chatId))
    .orderBy(messages.createdAt);

  return { chat, messages: chatMessages };
}

/**
 * Save a message to a chat
 */
export async function saveMessage(
  chatId: string,
  role: 'user' | 'assistant' | 'system' | 'function',
  content: string,
  thinkingContent?: string,
  toolCallsData?: any[]
): Promise<Message> {
  const [message] = await db.insert(messages).values({
    chatId,
    role,
    content,
    thinkingContent,
    toolCalls: toolCallsData,
  }).returning();

  // Update chat's updatedAt
  await db.update(chats)
    .set({ updatedAt: new Date() })
    .where(eq(chats.id, chatId));

  revalidatePath(`/chat/${chatId}`);
  return message;
}

/**
 * Save tool result
 */
export async function saveToolResult(
  messageId: string,
  toolCallId: string,
  toolName: string,
  output: string,
  metadata?: Record<string, any>
) {
  await db.insert(toolResults).values({
    messageId,
    toolCallId,
    toolName,
    output,
    metadata,
  });
}

/**
 * Update chat title
 */
export async function updateChatTitle(chatId: string, title: string): Promise<void> {
  await db.update(chats)
    .set({ title, updatedAt: new Date() })
    .where(eq(chats.id, chatId));

  revalidatePath('/');
  revalidatePath(`/chat/${chatId}`);
}

/**
 * Delete a chat
 */
export async function deleteChat(chatId: string): Promise<void> {
  await db.delete(chats).where(eq(chats.id, chatId));
  revalidatePath('/');
}

/**
 * Get messages for streaming (format for backend)
 */
export async function getMessagesForBackend(chatId: string): Promise<Array<{ role: string; content: string }>> {
  const chatMessages = await db
    .select()
    .from(messages)
    .where(eq(messages.chatId, chatId))
    .orderBy(messages.createdAt);

  return chatMessages.map(msg => ({
    role: msg.role,
    content: msg.content,
  }));
}

