import { Analysis } from '@/types'
import { BookOpen, FileText, ListChecks } from 'lucide-react'

interface PlaybookPanelProps {
  analysis: Analysis | null
}

export default function PlaybookPanel({ analysis }: PlaybookPanelProps) {
  const playbook = analysis?.playbook_result ?? null

  if (!analysis || !playbook) {
    return (
      <div className="flex flex-col items-center justify-center py-6 text-center px-4">
        <BookOpen size={18} className="text-slate-700 mb-2" />
        <p className="text-xs text-slate-600">
          Playbook context will appear here after analysis.
        </p>
      </div>
    )
  }

  const hasActions = (playbook.recommended_actions?.length ?? 0) > 0
  const hasSources = (playbook.sources?.length ?? 0) > 0

  return (
    <div className="space-y-3">
      {/* Playbook name + match reason */}
      <div className="rounded-md border border-slate-800/80 bg-slate-900/50 p-3">
        <div className="flex items-center gap-1.5 mb-1">
          <BookOpen size={11} className="text-blue-400 shrink-0" />
          <span className="text-[10px] font-semibold text-slate-500 uppercase tracking-widest">
            Playbook
          </span>
        </div>
        <p className="text-xs font-semibold text-slate-200 mb-1">{playbook.playbook_name}</p>
        {playbook.match_reason && (
          <p className="text-[11px] text-slate-400 leading-relaxed">{playbook.match_reason}</p>
        )}
      </div>

      {/* Recommended actions */}
      {hasActions && (
        <div className="rounded-md border border-slate-800/80 bg-slate-900/50 p-3">
          <div className="flex items-center gap-1.5 mb-2">
            <ListChecks size={11} className="text-emerald-400 shrink-0" />
            <span className="text-[10px] font-semibold text-slate-500 uppercase tracking-widest">
              Recommended actions
            </span>
          </div>
          <ul className="space-y-1.5">
            {playbook.recommended_actions.map((action, i) => (
              <li key={i} className="flex items-start gap-2 text-xs text-slate-300 leading-relaxed">
                <span className="text-emerald-600 mt-0.5 shrink-0">{i + 1}.</span>
                <span>{action}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Sources */}
      {hasSources && (
        <div className="rounded-md border border-slate-800/80 bg-slate-900/50 p-3">
          <div className="flex items-center gap-1.5 mb-2">
            <FileText size={11} className="text-blue-400 shrink-0" />
            <span className="text-[10px] font-semibold text-slate-500 uppercase tracking-widest">
              Sources used for retrieval
            </span>
          </div>
          <ul className="space-y-1.5">
            {playbook.sources.map((src, i) => (
              <li
                key={i}
                className="flex items-center gap-2 text-[11px] font-mono text-slate-400"
              >
                <span className="text-slate-600">•</span>
                <span className="truncate" title={src.file}>
                  {src.file.split(/[/\\]/).pop() || src.file}
                </span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}
