import { Analysis } from '@/types'
import { BookOpen, ExternalLink } from 'lucide-react'

interface PlaybookPanelProps {
  analysis: Analysis | null
}

export default function PlaybookPanel({ analysis }: PlaybookPanelProps) {
  const hasStructuredSources = (analysis?.playbook_sources?.length ?? 0) > 0
  const hasPlaybookContext = !!analysis?.playbook_context?.trim()

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

  if (hasStructuredSources && analysis.playbook_sources) {
    return (
      <div className="space-y-2">
        {analysis.playbook_sources.map((pb, i) => (
          <div
            key={i}
            className="rounded-md border border-slate-800/80 bg-slate-900/50 p-3 space-y-1.5"
          >
            <div className="flex items-start justify-between gap-2">
              <div className="flex items-center gap-1.5">
                <BookOpen size={11} className="text-blue-400 shrink-0 mt-0.5" />
                <span className="text-xs font-semibold text-slate-200">{pb.title}</span>
              </div>
              <ExternalLink size={10} className="text-slate-600 shrink-0 mt-0.5" />
            </div>
            <div className="flex items-center gap-1">
              <span className="text-[9px] text-slate-600 uppercase tracking-widest">Source:</span>
              <span className="text-[10px] text-slate-500">{pb.source}</span>
            </div>
            <p className="text-[11px] text-slate-400 leading-relaxed border-l-2 border-slate-700 pl-2 italic">
              {pb.excerpt}
            </p>
            {pb.relevance && (
              <div className="pt-1 border-t border-slate-800/60">
                <span className="text-[9px] text-slate-600 uppercase tracking-widest">
                  Why retrieved:{' '}
                </span>
                <span className="text-[10px] text-slate-500">{pb.relevance}</span>
              </div>
            )}
          </div>
        ))}
      </div>
    )
  }

  if (hasPlaybookContext) {
    return (
      <div className="rounded-md border border-slate-800/80 bg-slate-900/50 p-3">
        <div className="flex items-center gap-1.5 mb-2">
          <BookOpen size={11} className="text-blue-400 shrink-0" />
          <span className="text-[10px] font-semibold text-slate-500 uppercase tracking-widest">
            Playbook guidance
          </span>
        </div>
        <div className="text-xs text-slate-300 leading-relaxed whitespace-pre-wrap">
          {analysis.playbook_context}
        </div>
      </div>
    )
  }

  return (
    <div className="flex flex-col items-center justify-center py-6 text-center px-4">
      <BookOpen size={18} className="text-slate-700 mb-2" />
      <p className="text-xs text-slate-600">
        Playbook context will appear here after analysis.
      </p>
    </div>
  )
}
