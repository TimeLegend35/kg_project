/**
 * BGB Chat Database Schema - Drizzle ORM
 * Speichert Chat History im Frontend
 */
import { pgTable, text, timestamp, uuid, json, integer } from 'drizzle-orm/pg-core';

// Chat Sessions
export const chats = pgTable('bgb_chats', {
  id: uuid('id').primaryKey().defaultRandom(),
  userId: text('user_id').notNull().default('default_user'),
  title: text('title').notNull().default('Neue Unterhaltung'),
  createdAt: timestamp('created_at').notNull().defaultNow(),
  updatedAt: timestamp('updated_at').notNull().defaultNow(),
});

// Chat Messages
export const messages = pgTable('bgb_messages', {
  id: uuid('id').primaryKey().defaultRandom(),
  chatId: uuid('chat_id').notNull().references(() => chats.id, { onDelete: 'cascade' }),
  role: text('role', { enum: ['user', 'assistant', 'system', 'function'] }).notNull(),
  content: text('content').notNull(),
  thinkingContent: text('thinking_content'),
  toolCalls: json('tool_calls').$type<Array<{
    id: string;
    name: string;
    arguments: Record<string, any>;
    status: string;
  }>>(),
  metadata: json('metadata').$type<Record<string, any>>(),
  createdAt: timestamp('created_at').notNull().defaultNow(),
});

// Tool Call Results (separate für bessere Query Performance)
export const toolResults = pgTable('bgb_tool_results', {
  id: uuid('id').primaryKey().defaultRandom(),
  messageId: uuid('message_id').notNull().references(() => messages.id, { onDelete: 'cascade' }),
  toolCallId: text('tool_call_id').notNull(),
  toolName: text('tool_name').notNull(),
  output: text('output').notNull(),
  metadata: json('metadata').$type<Record<string, any>>(),
  createdAt: timestamp('created_at').notNull().defaultNow(),
});

export type Chat = typeof chats.$inferSelect;
export type NewChat = typeof chats.$inferInsert;
export type Message = typeof messages.$inferSelect;
export type NewMessage = typeof messages.$inferInsert;
export type ToolResult = typeof toolResults.$inferSelect;
export type NewToolResult = typeof toolResults.$inferInsert;

