import { useState, useCallback } from 'react'
import { Message, Alert } from '@/types'

export function useIncidentChat(alert: Alert | null) {
  const [messages, setMessages] = useState<Message[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [status, setStatus] = useState<string>('')

  const sendMessage = useCallback(
    async (content: string) => {
      if (!content.trim() || isLoading) return

      const userMessage: Message = {
        id: `user-${Date.now()}`,
        role: 'user',
        content: content.trim(),
        timestamp: new Date(),
      }

      const updatedMessages = [...messages, userMessage]
      setMessages(updatedMessages)
      setIsLoading(true)
      setStatus('')

      const assistantId = `assistant-${Date.now() + 1}`
      const assistantMessage: Message = {
        id: assistantId,
        role: 'assistant',
        content: '',
        timestamp: new Date(),
      }
      setMessages([...updatedMessages, assistantMessage])

      const systemContext = alert
        ? `You are a SOC analyst assistant. The analyst is currently investigating the following incident:\n\nIncident: ${alert.title}\nSeverity: ${alert.severity}\nSource IP: ${alert.source_ip}\nDestination IP: ${alert.dest_ip}\n\nRaw Logs:\n${alert.raw_log}\n\nAnswer follow-up questions about this incident concisely and accurately.`
        : 'You are a SOC analyst assistant. Answer security questions concisely.'

      const contextMessage: Message = {
        id: 'system-context',
        role: 'user',
        content: systemContext,
      } as Message

      try {
        const response = await fetch('/api/chat', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            messages: [contextMessage, ...updatedMessages].map(({ role, content }) => ({
              role,
              content,
            })),
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
    [messages, isLoading, alert]
  )

  const clearMessages = useCallback(() => {
    setMessages([])
    setStatus('')
  }, [])

  return { messages, isLoading, status, sendMessage, clearMessages }
}
