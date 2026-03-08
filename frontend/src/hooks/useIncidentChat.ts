import { useState, useCallback, useEffect, useRef } from 'react'
import { Alert, Analysis, Message } from '@/types'

export interface UseIncidentChatOptions {
  /** The active alert (for case context sent to API). */
  alert: Alert | null
  /** The structured analysis result from the dashboard (passed as context to the API). */
  analysis: Analysis | null
  /** Identity for the current conversation. When this changes, messages reset. */
  conversationId?: string | null
}

/**
 * Incident/copilot chat with case-aware context.
 *
 * Sends the full structured case state (triage_result, playbook_result, conversation_history)
 * to /api/chat on each turn. The router decides whether existing results suffice or new
 * specialist work is needed.
 *
 * Only the follow-up Q&A messages are displayed; the analysis context is sent API-only.
 */
export function useIncidentChat(options: UseIncidentChatOptions) {
  const { alert, analysis, conversationId = null } = options

  const [messages, setMessages] = useState<Message[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [status, setStatus] = useState<string>('')
  const prevConversationIdRef = useRef<string | null>(null)

  // Reset displayed messages when conversationId changes (new analysis or alert switch)
  useEffect(() => {
    if (conversationId !== prevConversationIdRef.current) {
      prevConversationIdRef.current = conversationId
      setMessages([])
    }
  }, [conversationId])

  const sendMessage = useCallback(
    async (content: string) => {
      if (!content.trim() || isLoading) return

      const userMessage: Message = {
        id: `user-${Date.now()}`,
        role: 'user',
        content: content.trim(),
        timestamp: new Date(),
      }

      const displayedMessages = [...messages, userMessage]
      setMessages(displayedMessages)
      setIsLoading(true)
      setStatus('')

      const assistantId = `assistant-${Date.now() + 1}`
      const assistantMessage: Message = {
        id: assistantId,
        role: 'assistant',
        content: '',
        timestamp: new Date(),
      }
      setMessages((prev) => [...prev, assistantMessage])

      // Build the conversation history from visible messages (prior Q&A turns only)
      const conversationHistory = displayedMessages.map((m) => ({
        role: m.role,
        content: m.content,
      }))

      const requestBody = {
        user_query: content.trim(),
        active_case_id: alert?.id ?? null,
        active_case_title: alert?.title ?? null,
        selected_log_data: alert
          ? {
              raw_log: alert.raw_log,
              source_ip: alert.source_ip,
              dest_ip: alert.dest_ip,
              title: alert.title,
              description: alert.description,
            }
          : null,
        triage_result: analysis?.triage_result ?? null,
        playbook_result: analysis?.playbook_result ?? null,
        conversation_history: conversationHistory,
      }

      try {
        const response = await fetch('/api/chat', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(requestBody),
        })

        if (!response.ok) {
          throw new Error(`Server error: ${response.status} ${response.statusText}`)
        }

        const reader = response.body!.getReader()
        const decoder = new TextDecoder()
        let buffer = ''

        while (true) {
          const { done, value } = await reader.read()
          if (done) break

          buffer += decoder.decode(value, { stream: true })
          const lines = buffer.split('\n')
          buffer = lines.pop() ?? ''

          for (const line of lines) {
            if (!line.startsWith('data: ')) continue
            const raw = line.slice(6).trim()
            if (!raw) continue

            try {
              const data = JSON.parse(raw)

              if (data.type === 'token') {
                setMessages((prev) =>
                  prev.map((msg) =>
                    msg.id === assistantId
                      ? { ...msg, content: msg.content + data.content }
                      : msg
                  )
                )
              } else if (data.type === 'status') {
                setStatus(data.content)
              } else if (data.type === 'result') {
                // result event carries updated triage/playbook - no display action needed here
              } else if (data.type === 'error') {
                setMessages((prev) =>
                  prev.map((msg) =>
                    msg.id === assistantId
                      ? { ...msg, content: `⚠️ An error occurred: ${data.content}` }
                      : msg
                  )
                )
                setStatus('')
                setIsLoading(false)
              } else if (data.type === 'done') {
                setStatus('')
                setIsLoading(false)
              }
            } catch {
              // skip malformed lines
            }
          }
        }
      } catch (error) {
        const errMsg = error instanceof Error ? error.message : 'Unknown error occurred'
        setMessages((prev) =>
          prev.map((msg) =>
            msg.id === assistantId
              ? { ...msg, content: `⚠️ Failed to reach the server: ${errMsg}` }
              : msg
          )
        )
      } finally {
        setIsLoading(false)
        setStatus('')
      }
    },
    [messages, isLoading, alert, analysis]
  )

  const clearMessages = useCallback(() => {
    setMessages([])
    setStatus('')
  }, [])

  return { messages, isLoading, status, sendMessage, clearMessages }
}
