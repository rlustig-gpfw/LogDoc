import { useRef, useEffect, useState, KeyboardEvent } from 'react'
import { Alert, Message } from '@/types'
import { useIncidentChat } from '@/hooks/useIncidentChat'
import MessageBubble from '@/components/MessageBubble'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Textarea } from '@/components/ui/textarea'
import { Button } from '@/components/ui/button'
import {
  MessageCircle,
  SendHorizonal,
  Loader2,
  Database,
  Globe,
  ChevronRight,
  Trash2,
} from 'lucide-react'

interface CopilotChatProps {
  alert: Alert | null
  /** Message history from the analysis (user prompt + assistant response). Chat uses this as context; no extra data is sent. */
  initialMessages?: Message[] | null
  /** When this changes, the chat resets to initialMessages. */
  conversationId?: string | null
}

const QUICK_PROMPTS = [
  'Summarize for escalation',
  'What is the MITRE technique?',
  'Recommended containment steps?',
]

function StatusPill({ status }: { status: string }) {
  if (!status) return null
  const isKB = status.toLowerCase().includes('knowledge base')
  const isWeb = status.toLowerCase().includes('web')
  return (
    <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-slate-800/90 border border-slate-700/60 w-fit mx-auto">
      {isKB && <Database size={10} className="text-blue-400 animate-pulse" />}
      {isWeb && <Globe size={10} className="text-emerald-400 animate-pulse" />}
      {!isKB && !isWeb && <ChevronRight size={10} className="text-slate-400 animate-pulse" />}
      <span className="text-[10px] text-slate-400">{status}</span>
    </div>
  )
}

export default function CopilotChat({
  alert,
  initialMessages = null,
  conversationId = null,
}: CopilotChatProps) {
  const { messages, isLoading, status, sendMessage, clearMessages } = useIncidentChat({
    initialMessages,
    conversationId,
  })
  const [value, setValue] = useState('')
  const scrollViewportRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const viewport = scrollViewportRef.current
    if (viewport) viewport.scrollTop = viewport.scrollHeight
  }, [messages, status])

  const handleSend = () => {
    const trimmed = value.trim()
    if (!trimmed || isLoading) return
    sendMessage(trimmed)
    setValue('')
  }

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const lastIsAssistant =
    messages.length > 0 && messages[messages.length - 1].role === 'assistant'

  return (
    <div className="flex flex-col h-full bg-slate-950 border-l border-slate-800/80">
      {/* Panel header */}
      <div className="shrink-0 flex items-center justify-between px-3 py-3 border-b border-slate-800/80">
        <div className="flex items-center gap-2">
          <MessageCircle size={12} className="text-blue-400" />
          <span className="text-xs font-semibold text-slate-300 uppercase tracking-widest">
            AI Copilot
          </span>
        </div>
        {messages.length > 0 && (
          <button
            onClick={clearMessages}
            className="flex items-center gap-1 text-[10px] text-slate-600 hover:text-slate-400 transition-colors"
          >
            <Trash2 size={10} />
            Clear
          </button>
        )}
      </div>

      {/* Message area */}
      <div className="flex-1 overflow-hidden relative">
        {messages.length === 0 ? (
          <div className="flex flex-col h-full justify-end pb-3">
            <div className="px-3 mb-3">
              <div className="flex flex-col items-center justify-center py-6 text-center">
                <MessageCircle size={20} className="text-slate-700 mb-2" />
                <p className="text-xs text-slate-600">
                  {alert
                    ? 'Ask follow-up questions about this incident.'
                    : 'Select an alert to start chatting.'}
                </p>
              </div>

              {alert && (
                <div className="space-y-1.5">
                  {QUICK_PROMPTS.map((p) => (
                    <button
                      key={p}
                      onClick={() => sendMessage(p)}
                      disabled={isLoading}
                      className="w-full text-left px-2.5 py-1.5 rounded border border-slate-800 bg-slate-900/60 hover:bg-slate-800/60 text-[11px] text-slate-400 hover:text-slate-300 transition-colors"
                    >
                      {p}
                    </button>
                  ))}
                </div>
              )}
            </div>
          </div>
        ) : (
          <ScrollArea className="h-full" ref={scrollViewportRef}>
            <div className="flex flex-col gap-3 px-3 py-3">
              {messages.map((message, index) => (
                <MessageBubble
                  key={message.id}
                  message={message}
                  isStreaming={
                    isLoading &&
                    index === messages.length - 1 &&
                    message.role === 'assistant'
                  }
                />
              ))}
              {isLoading && lastIsAssistant && <StatusPill status={status} />}
              <div className="h-1" aria-hidden />
            </div>
          </ScrollArea>
        )}
      </div>

      {/* Input */}
      <div className="shrink-0 p-2.5 border-t border-slate-800/80 bg-slate-900/60">
        <div className="flex items-end gap-2">
          <Textarea
            value={value}
            onChange={(e) => setValue(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={alert ? 'Ask about this incident…' : 'Select an alert first…'}
            disabled={!alert || isLoading}
            rows={1}
            className="flex-1 min-h-[36px] max-h-[120px] py-2 text-xs bg-slate-900 border-slate-700 text-slate-100 placeholder:text-slate-600 focus-visible:ring-blue-500/40 resize-none leading-relaxed"
          />
          <Button
            onClick={handleSend}
            disabled={!value.trim() || isLoading || !alert}
            size="icon"
            className="h-9 w-9 shrink-0 bg-blue-600 hover:bg-blue-500 disabled:opacity-30"
          >
            {isLoading ? (
              <Loader2 size={14} className="animate-spin" />
            ) : (
              <SendHorizonal size={14} />
            )}
          </Button>
        </div>
      </div>
    </div>
  )
}
