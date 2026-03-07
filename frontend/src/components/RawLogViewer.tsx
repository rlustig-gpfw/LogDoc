import { useState } from 'react'
import { ChevronDown, ChevronRight, Copy, Check } from 'lucide-react'
import { cn } from '@/lib/utils'

interface RawLogViewerProps {
  rawLog: string
}

export default function RawLogViewer({ rawLog }: RawLogViewerProps) {
  const [isExpanded, setIsExpanded] = useState(true)
  const [copied, setCopied] = useState(false)

  const handleCopy = async () => {
    await navigator.clipboard.writeText(rawLog)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <div className="rounded-md border border-slate-800/80 overflow-hidden">
      <button
        onClick={() => setIsExpanded((v) => !v)}
        className="w-full flex items-center justify-between px-3 py-2 bg-slate-900/80 hover:bg-slate-800/60 transition-colors"
      >
        <div className="flex items-center gap-2">
          {isExpanded ? (
            <ChevronDown size={12} className="text-slate-500" />
          ) : (
            <ChevronRight size={12} className="text-slate-500" />
          )}
          <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-widest">
            Raw Evidence
          </span>
          <span className="text-[10px] text-slate-600">
            {rawLog.split('\n').length} lines
          </span>
        </div>
        {isExpanded && (
          <button
            onClick={(e) => {
              e.stopPropagation()
              handleCopy()
            }}
            className="flex items-center gap-1 px-2 py-0.5 rounded text-[10px] text-slate-500 hover:text-slate-300 hover:bg-slate-700/50 transition-colors"
          >
            {copied ? (
              <Check size={10} className="text-emerald-400" />
            ) : (
              <Copy size={10} />
            )}
            {copied ? 'Copied' : 'Copy'}
          </button>
        )}
      </button>

      {isExpanded && (
        <div className="bg-slate-950/80 p-3 overflow-x-auto max-h-48">
          <pre className="text-[10px] font-mono text-slate-400 leading-relaxed whitespace-pre-wrap break-all">
            {rawLog}
          </pre>
        </div>
      )}
    </div>
  )
}
