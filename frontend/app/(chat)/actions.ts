"use server";

import type { UIMessage } from "ai";
import { cookies } from "next/headers";
import type { VisibilityType } from "@/components/visibility-selector";
import { generateTitleWithBackend } from "@/lib/ai/bgb-provider";
import {
  deleteMessagesByChatIdAfterTimestamp,
  getMessageById,
  updateChatVisiblityById,
} from "@/lib/db/queries";

export async function saveChatModelAsCookie(model: string) {
  const cookieStore = await cookies();
  cookieStore.set("chat-model", model);
}

/**
 * Generiere Titel mit unserem FastAPI Backend (gleiches Endpoint wie Chat)
 */
export async function generateTitleFromUserMessage({
  message,
  chatId,
}: {
  message: UIMessage;
  chatId?: string;
}) {
  // Nutze unser FastAPI Backend für Title Generation
  const messageContent = typeof message.content === 'string'
    ? message.content
    : JSON.stringify(message.content);

  const title = await generateTitleWithBackend(
    chatId || 'temp-title-gen',
    messageContent
  );

  return title;
}

export async function deleteTrailingMessages({ id }: { id: string }) {
  const [message] = await getMessageById({ id });

  await deleteMessagesByChatIdAfterTimestamp({
    chatId: message.chatId,
    timestamp: message.createdAt,
  });
}

export async function updateChatVisibility({
  chatId,
  visibility,
}: {
  chatId: string;
  visibility: VisibilityType;
}) {
  await updateChatVisiblityById({ chatId, visibility });
}
