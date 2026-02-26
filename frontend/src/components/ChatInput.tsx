import { useState, useRef, useCallback, KeyboardEvent } from 'react'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'
import { SendHorizonal, Loader2 } from 'lucide-react'

interface ChatInputProps {
  onSend: (message: string) => void
  isLoading: boolean
  disabled?: boolean
}

export default function ChatInput({ onSend, isLoading, disabled }: ChatInputProps) {
  const [value, setValue] = useState('')
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  const handleSend = useCallback(() => {
    const trimmed = value.trim()
    if (!trimmed || isLoading) return
    onSend(trimmed)
    setValue('')
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
    }
  }, [value, isLoading, onSend])

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const handleInput = () => {
    const el = textareaRef.current
    if (!el) return
    el.style.height = 'auto'
    el.style.height = `${Math.min(el.scrollHeight, 200)}px`
  }

  return (
    <div className="relative flex items-end gap-2.5 p-4 bg-slate-900/80 border-t border-slate-800 backdrop-blur-sm">
      <Textarea
        ref={textareaRef}
        value={value}
        onChange={(e) => setValue(e.target.value)}
        onKeyDown={handleKeyDown}
        onInput={handleInput}
        placeholder="Ask about network activity, paste Zeek logs, or describe an incident…"
        disabled={disabled || isLoading}
        rows={1}
        className="flex-1 min-h-[44px] max-h-[200px] py-3 bg-slate-900 border-slate-700 text-slate-100 placeholder:text-slate-500 focus-visible:ring-blue-500/40 focus-visible:border-blue-600/60 resize-none leading-relaxed"
      />
      <Button
        onClick={handleSend}
        disabled={!value.trim() || isLoading || disabled}
        size="icon"
        className="h-[44px] w-[44px] shrink-0 bg-blue-600 hover:bg-blue-500 disabled:opacity-30 shadow-lg shadow-blue-900/30 transition-all duration-200"
        aria-label="Send message"
      >
        {isLoading ? (
          <Loader2 size={17} className="animate-spin" />
        ) : (
          <SendHorizonal size={17} />
        )}
      </Button>
      <p className="absolute bottom-1.5 left-4 text-[10px] text-slate-600">
        Enter to send · Shift+Enter for new line
      </p>
    </div>
  )
}
