import { Alert } from '@/types'
import { ScrollArea } from '@/components/ui/scroll-area'
import AlertCard from '@/components/AlertCard'
import { Play, Radio } from 'lucide-react'
import { cn } from '@/lib/utils'

interface AlertFeedProps {
  alerts: Alert[]
  selectedAlertId: string | null
  onSelectAlert: (alert: Alert) => void
  onStartDemoStream: () => void
  isDemoStreaming: boolean
  severityFilter: string
  onSeverityFilterChange: (filter: string) => void
}

const SEVERITY_FILTERS = ['all', 'high', 'medium', 'low']

export default function AlertFeed({
  alerts,
  selectedAlertId,
  onSelectAlert,
  onStartDemoStream,
  isDemoStreaming,
  severityFilter,
  onSeverityFilterChange,
}: AlertFeedProps) {
  const filtered =
    severityFilter === 'all' ? alerts : alerts.filter((a) => a.severity === severityFilter)

  return (
    <div className="flex flex-col h-full bg-slate-950 border-r border-slate-800/80">
      {/* Panel header */}
      <div className="shrink-0 px-3 py-3 border-b border-slate-800/80">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <span className="text-xs font-semibold text-slate-300 uppercase tracking-widest">
              Alert Feed
            </span>
            <span className="inline-flex items-center justify-center h-4 min-w-4 px-1 rounded bg-slate-700 text-[10px] text-slate-300 font-mono">
              {alerts.length}
            </span>
          </div>
          <button
            onClick={onStartDemoStream}
            className={cn(
              'flex items-center gap-1.5 px-2 py-1 rounded text-[10px] font-medium transition-colors',
              isDemoStreaming
                ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                : 'bg-blue-600/20 text-blue-400 border border-blue-500/30 hover:bg-blue-600/30'
            )}
          >
            {isDemoStreaming ? (
              <>
                <Radio size={10} className="animate-pulse" />
                Streaming
              </>
            ) : (
              <>
                <Play size={10} />
                Demo Stream
              </>
            )}
          </button>
        </div>

        {/* Severity filter tabs */}
        <div className="flex gap-1">
          {SEVERITY_FILTERS.map((f) => (
            <button
              key={f}
              onClick={() => onSeverityFilterChange(f)}
              className={cn(
                'px-2 py-0.5 rounded text-[10px] font-medium capitalize transition-colors',
                severityFilter === f
                  ? 'bg-slate-700 text-slate-200'
                  : 'text-slate-500 hover:text-slate-400'
              )}
            >
              {f}
            </button>
          ))}
        </div>
      </div>

      {/* Alert list */}
      <ScrollArea className="flex-1">
        <div className="p-2 space-y-1.5">
          {filtered.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-10 text-center px-3">
              <Radio size={20} className="text-slate-700 mb-2" />
              <p className="text-xs text-slate-600">No alerts match this filter.</p>
            </div>
          ) : (
            filtered.map((alert) => (
              <AlertCard
                key={alert.id}
                alert={alert}
                isSelected={alert.id === selectedAlertId}
                onClick={() => onSelectAlert(alert)}
              />
            ))
          )}
        </div>
      </ScrollArea>
    </div>
  )
}
