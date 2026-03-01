import { useEffect, useRef } from 'react'
import { ShieldCheck, Trash2, Database, Globe, ChevronRight } from 'lucide-react'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Separator } from '@/components/ui/separator'
import MessageBubble from '@/components/MessageBubble'
import ChatInput from '@/components/ChatInput'
import WelcomeScreen from '@/components/WelcomeScreen'
import { useChat } from '@/hooks/useChat'

function StatusBar({ status }: { status: string }) {
  if (!status) return null

  const isSearchingKB = status.toLowerCase().includes('knowledge base')
  const isSearchingWeb = status.toLowerCase().includes('web')

  return (
    <div className="flex items-center justify-center py-2 px-4">
      <div className="flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-slate-800/90 border border-slate-700/60 shadow-sm">
        {isSearchingKB && <Database size={12} className="text-blue-400 animate-pulse" />}
        {isSearchingWeb && <Globe size={12} className="text-emerald-400 animate-pulse" />}
        {!isSearchingKB && !isSearchingWeb && (
          <ChevronRight size={12} className="text-slate-400 animate-pulse" />
        )}
        <span className="text-xs text-slate-400">{status}</span>
      </div>
    </div>
  )
}

export default function ChatInterface() {
  const { messages, isLoading, status, sendMessage, clearMessages } = useChat()
  const scrollViewportRef = useRef<HTMLDivElement>(null)

  // Auto-scroll to bottom on new messages or streaming content (scroll viewport directly so we don't steal focus from the input)
  useEffect(() => {
    const viewport = scrollViewportRef.current
    if (viewport) viewport.scrollTop = viewport.scrollHeight
  }, [messages, status])

  const handlePromptSelect = (prompt: string) => {
    sendMessage(prompt)
  }

  const lastMessageIsAssistant =
    messages.length > 0 && messages[messages.length - 1].role === 'assistant'

  return (
    <div className="flex flex-col h-screen bg-slate-950">
      {/* ── Header ── */}
      <header className="shrink-0 flex items-center justify-between px-5 py-3.5 bg-slate-900 border-b border-slate-800/80 shadow-md shadow-black/20 z-10">
        <div className="flex items-center gap-3">
          <div className="flex items-center justify-center h-8 w-8 rounded-lg bg-gradient-to-br from-blue-600 to-blue-700 shadow shadow-blue-900/40">
            <ShieldCheck size={16} className="text-white" strokeWidth={2} />
          </div>
          <div className="flex items-baseline gap-2.5">
            <span className="font-semibold text-slate-100 tracking-tight text-[15px]">
              LogDoc
            </span>
            <Badge variant="default" className="text-[10px] px-2 py-0 h-4">
              SOC Triage Agent
            </Badge>
          </div>
        </div>

        <div className="flex items-center gap-3">
          {/* Online indicator */}
          <div className="flex items-center gap-1.5">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-50" />
              <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500" />
            </span>
            <span className="text-[11px] text-slate-500">Online</span>
          </div>

          <Separator orientation="vertical" className="h-4" />

          {messages.length > 0 && (
            <Button
              variant="ghost"
              size="sm"
              onClick={clearMessages}
              className="text-slate-500 hover:text-slate-300 gap-1.5 text-xs h-7 px-2"
            >
              <Trash2 size={12} />
              Clear
            </Button>
          )}
        </div>
      </header>

      {/* ── Message area ── */}
      <div className="flex-1 overflow-hidden relative">
        {messages.length === 0 ? (
          <WelcomeScreen onPromptSelect={handlePromptSelect} />
        ) : (
          <ScrollArea className="h-full" ref={scrollViewportRef}>
            <div className="flex flex-col gap-5 px-4 py-6 max-w-3xl mx-auto w-full">
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

              {/* Tool status indicator */}
              {isLoading && lastMessageIsAssistant && (
                <StatusBar status={status} />
              )}

              <div className="h-1" aria-hidden />
            </div>
          </ScrollArea>
        )}

        {/* Gradient fade at top of message area */}
        {messages.length > 0 && (
          <div className="absolute top-0 left-0 right-0 h-6 bg-gradient-to-b from-slate-950 to-transparent pointer-events-none z-10" />
        )}
      </div>

      {/* ── Input area ── */}
      <div className="shrink-0">
        <ChatInput
          onSend={sendMessage}
          isLoading={isLoading}
        />
      </div>
    </div>
  )
}
