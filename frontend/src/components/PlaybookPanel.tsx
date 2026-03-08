import { Analysis } from '@/types'
import { BookOpen, FileText } from 'lucide-react'

interface PlaybookPanelProps {
  analysis: Analysis | null
}

export default function PlaybookPanel({ analysis }: PlaybookPanelProps) {
  const hasPlaybookContext = !!analysis?.playbook_context?.trim()
  const hasSources = (analysis?.playbook_sources?.length ?? 0) > 0
  const sources = analysis?.playbook_sources ?? []

  if (!analysis) {
    return (
      <div className="flex flex-col items-center justify-center py-6 text-center px-4">
        <BookOpen size={18} className="text-slate-700 mb-2" />
        <p className="text-xs text-slate-600">
          Playbook context will appear here after analysis.
        </p>
      </div>
    )
  }

  if (!hasPlaybookContext && !hasSources) {
    return (
      <div className="flex flex-col items-center justify-center py-6 text-center px-4">
        <BookOpen size={18} className="text-slate-700 mb-2" />
        <p className="text-xs text-slate-600">
          Playbook context will appear here after analysis.
        </p>
      </div>
    )
  }

  return (
    <div className="space-y-3">
      {hasPlaybookContext && (
        <div className="rounded-md border border-slate-800/80 bg-slate-900/50 p-3">
          <div className="flex items-center gap-1.5 mb-2">
            <BookOpen size={11} className="text-blue-400 shrink-0" />
            <span className="text-[10px] font-semibold text-slate-500 uppercase tracking-widest">
              Playbook context
            </span>
          </div>
          <div className="text-xs text-slate-300 leading-relaxed whitespace-pre-wrap">
            {analysis.playbook_context}
          </div>
        </div>
      )}

      {hasSources && (
        <div className="rounded-md border border-slate-800/80 bg-slate-900/50 p-3">
          <div className="flex items-center gap-1.5 mb-2">
            <FileText size={11} className="text-blue-400 shrink-0" />
            <span className="text-[10px] font-semibold text-slate-500 uppercase tracking-widest">
              Sources used for retrieval
            </span>
          </div>
          <ul className="space-y-1.5">
            {sources.map((pb, i) => (
              <li
                key={i}
                className="flex items-center gap-2 text-[11px] font-mono text-slate-400"
              >
                <span className="text-slate-600">•</span>
                <span className="truncate" title={pb.source}>
                  {pb.title || pb.source}
                </span>
                {pb.source !== (pb.title || pb.source) && (
                  <span className="text-slate-600 truncate shrink" title={pb.source}>
                    ({pb.source})
                  </span>
                )}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}
