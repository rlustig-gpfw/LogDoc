import { Alert } from '@/types'
import { cn } from '@/lib/utils'
import { AlertTriangle, Shield, Info, Clock, ArrowRight } from 'lucide-react'
import { Badge } from '@/components/ui/badge'

interface AlertCardProps {
  alert: Alert
  isSelected: boolean
  onClick: () => void
}

const SEVERITY_CONFIG = {
  high: {
    badge: 'bg-red-500/20 text-red-400 border-red-500/30',
    border: 'border-l-red-500',
    icon: AlertTriangle,
    iconClass: 'text-red-400',
    label: 'High',
  },
  medium: {
    badge: 'bg-amber-500/20 text-amber-400 border-amber-500/30',
    border: 'border-l-amber-500',
    icon: Shield,
    iconClass: 'text-amber-400',
    label: 'Medium',
  },
  low: {
    badge: 'bg-blue-500/20 text-blue-400 border-blue-500/30',
    border: 'border-l-blue-500',
    icon: Info,
    iconClass: 'text-blue-400',
    label: 'Low',
  },
}

const STATUS_CONFIG = {
  new: 'bg-emerald-500/15 text-emerald-400 border-emerald-500/25',
  triaged: 'bg-blue-500/15 text-blue-400 border-blue-500/25',
  escalated: 'bg-orange-500/15 text-orange-400 border-orange-500/25',
  resolved: 'bg-slate-500/15 text-slate-400 border-slate-500/25',
}

export default function AlertCard({ alert, isSelected, onClick }: AlertCardProps) {
  const sev = SEVERITY_CONFIG[alert.severity]
  const SevIcon = sev.icon

  return (
    <button
      onClick={onClick}
      className={cn(
        'w-full text-left px-3 py-2.5 rounded-md border-l-2 transition-all duration-150',
        'bg-slate-900/60 hover:bg-slate-800/80 border border-slate-800/80',
        sev.border,
        isSelected && 'bg-slate-800/90 ring-1 ring-blue-500/40 border-slate-700/80'
      )}
    >
      <div className="flex items-start justify-between gap-2 mb-1.5">
        <div className="flex items-center gap-1.5 min-w-0">
          <SevIcon size={12} className={cn('shrink-0', sev.iconClass)} />
          <span className="text-xs font-medium text-slate-200 truncate">{alert.title}</span>
        </div>
        {isSelected && <ArrowRight size={11} className="shrink-0 text-blue-400 mt-0.5" />}
      </div>

      <div className="flex items-center gap-1.5 mb-1.5">
        <Clock size={10} className="text-slate-600 shrink-0" />
        <span className="text-[10px] text-slate-500 font-mono">{alert.timestamp}</span>
      </div>

      <div className="flex items-center gap-1.5 mb-2">
        <span
          className={cn(
            'inline-flex items-center px-1.5 py-0.5 rounded text-[9px] font-medium border',
            sev.badge
          )}
        >
          {sev.label}
        </span>
        <span
          className={cn(
            'inline-flex items-center px-1.5 py-0.5 rounded text-[9px] font-medium border capitalize',
            STATUS_CONFIG[alert.status]
          )}
        >
          {alert.status}
        </span>
      </div>

      <div className="space-y-0.5">
        <div className="flex items-center gap-1">
          <span className="text-[9px] text-slate-600 w-6 shrink-0">SRC</span>
          <span className="text-[10px] text-slate-400 font-mono truncate">{alert.source_ip}</span>
        </div>
        <div className="flex items-center gap-1">
          <span className="text-[9px] text-slate-600 w-6 shrink-0">DST</span>
          <span className="text-[10px] text-slate-400 font-mono truncate">{alert.dest_ip}</span>
        </div>
      </div>
    </button>
  )
}
