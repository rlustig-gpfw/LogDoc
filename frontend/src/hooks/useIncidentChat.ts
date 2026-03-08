import { Message } from '@/types'
import { useChat, UseChatOptions } from '@/hooks/useChat'

export interface UseIncidentChatOptions {
  /** Seed the chat with the analysis conversation (user prompt + assistant response). No extra context is sent—this history is the context. */
  initialMessages?: Message[] | null
  /** Identity for the current conversation (e.g. alert id + analysis timestamp). When this changes, messages reset to initialMessages. */
  conversationId?: string | null
}

/**
 * Incident/copilot chat: analysis is sent to the API as context but not shown in the UI.
 * Only follow-up Q&A (e.g. "summarize the escalation" and the reply) are displayed.
 */
export function useIncidentChat(options: UseIncidentChatOptions = {}) {
  return useChat({
    initialMessages: options.initialMessages ?? null,
    conversationId: options.conversationId ?? null,
    contextOnlyForApi: true,
  })
}
