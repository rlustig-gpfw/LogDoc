import { useState, useCallback, useEffect, useRef } from 'react'
import { Message } from '@/types'

export interface UseChatOptions {
  /** Message history to include in API requests (e.g. analysis prompt + response). When contextOnlyForApi is true, these are not displayed. */
  initialMessages?: Message[] | null
  /** Identity for the current conversation. When this changes, display messages reset (or seed from initialMessages if not contextOnlyForApi). */
  conversationId?: string | null
  /** When true, initialMessages are sent to the API as context only and never shown in the UI. Display is only follow-up messages. */
  contextOnlyForApi?: boolean
}

export function useChat(options: UseChatOptions = {}) {
  const { initialMessages = null, conversationId = null, contextOnlyForApi = false } = options
  const [messages, setMessages] = useState<Message[]>(() =>
    contextOnlyForApi ? [] : (initialMessages ?? [])
  )
  const [isLoading, setIsLoading] = useState(false)
  const [status, setStatus] = useState<string>('')
  const prevConversationIdRef = useRef<string | null>(null)

  // When conversationId changes: reset display (or seed from initialMessages when not contextOnlyForApi)
  useEffect(() => {
    if (conversationId == null) {
      if (prevConversationIdRef.current != null) {
        prevConversationIdRef.current = null
        setMessages(contextOnlyForApi ? [] : (initialMessages ?? []))
      }
      return
    }
    if (conversationId !== prevConversationIdRef.current) {
      prevConversationIdRef.current = conversationId
      if (contextOnlyForApi) {
        setMessages([])
      } else if (initialMessages != null && initialMessages.length > 0) {
        setMessages(initialMessages.map((m) => ({ ...m, timestamp: m.timestamp ?? new Date() })))
      }
    }
  }, [conversationId, initialMessages, contextOnlyForApi])

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

      const contextForApi = (initialMessages ?? []).map((m) => ({ role: m.role, content: m.content }))
      const displayForApi = displayedMessages.map((m) => ({ role: m.role, content: m.content }))
      const payloadMessages = contextOnlyForApi ? [...contextForApi, ...displayForApi] : displayForApi

      try {
        const response = await fetch('/api/chat', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            messages: payloadMessages,
          }),
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
              } else if (data.type === 'error') {
                setMessages((prev) =>
                  prev.map((msg) =>
                    msg.id === assistantId
                      ? {
                          ...msg,
                          content: `⚠️ An error occurred: ${data.content}`,
                        }
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
        const errMsg =
          error instanceof Error ? error.message : 'Unknown error occurred'
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
    [messages, isLoading, initialMessages, contextOnlyForApi]
  )

  const clearMessages = useCallback(() => {
    setMessages(contextOnlyForApi ? [] : (initialMessages ?? []))
    setStatus('')
  }, [initialMessages, contextOnlyForApi])

  return { messages, isLoading, status, sendMessage, clearMessages }
}
