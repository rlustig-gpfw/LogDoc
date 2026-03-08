import { Analysis } from '@/types'
import { Target, Brain, Zap, Loader2 } from 'lucide-react'
import { cn } from '@/lib/utils'

interface TriageSummaryProps {
  analysis: Analysis | null
  isLoading: boolean
}

const CONFIDENCE_CONFIG = {
  high: 'text-emerald-400 bg-emerald-500/15 border-emerald-500/25',
  medium: 'text-amber-400 bg-amber-500/15 border-amber-500/25',
  low: 'text-red-400 bg-red-500/15 border-red-500/25',
}

function FieldCard({
  icon: Icon,
  label,
  children,
  className,
}: {
  icon: React.ElementType
  label: string
  children: React.ReactNode
  className?: string
}) {
  return (
    <div className={cn('rounded-md border border-slate-800/80 bg-slate-900/50 p-3', className)}>
      <div className="flex items-center gap-1.5 mb-1.5">
        <Icon size={11} className="text-slate-500" />
        <span className="text-[10px] font-semibold text-slate-500 uppercase tracking-widest">
          {label}
        </span>
      </div>
      {children}
    </div>
  )
}

export default function TriageSummary({ analysis, isLoading }: TriageSummaryProps) {
  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center py-8 gap-3">
        <Loader2 size={20} className="text-blue-400 animate-spin" />
        <p className="text-xs text-slate-500">Running AI triage analysis…</p>
      </div>
    )
  }

  if (!analysis) {
    return (
      <div className="flex flex-col items-center justify-center py-8 text-center px-4">
        <Brain size={20} className="text-slate-700 mb-2" />
        <p className="text-xs text-slate-600">
          Click <span className="text-slate-400 font-medium">Analyze</span> to run AI triage on
          this incident.
        </p>
      </div>
    )
  }

  const confidenceKey = analysis.confidence.toLowerCase() as keyof typeof CONFIDENCE_CONFIG
  const confidenceStyle = CONFIDENCE_CONFIG[confidenceKey] ?? CONFIDENCE_CONFIG.medium

  return (
    <div className="space-y-2">
      <div className="grid grid-cols-2 gap-2">
        <FieldCard icon={Target} label="Classification">
          <p className="text-sm font-semibold text-slate-200">{analysis.classification}</p>
        </FieldCard>

        <FieldCard icon={Zap} label="MITRE ATT&CK">
          <p className="text-sm font-semibold text-slate-200">{analysis.mitre_technique}</p>
        </FieldCard>
      </div>

      <div className="rounded-md border border-slate-800/80 bg-slate-900/50 p-3">
        <div className="flex items-center justify-between mb-1.5">
          <div className="flex items-center gap-1.5">
            <Brain size={11} className="text-slate-500" />
            <span className="text-[10px] font-semibold text-slate-500 uppercase tracking-widest">
              Confidence
            </span>
          </div>
          <span
            className={cn(
              'px-2 py-0.5 rounded text-[10px] font-medium border capitalize',
              confidenceStyle
            )}
          >
            {analysis.confidence}
          </span>
        </div>
        <p className="text-xs text-slate-300 leading-relaxed">{analysis.rationale}</p>
      </div>
    </div>
  )
}
