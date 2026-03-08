import { useState, useCallback } from 'react'
import { Alert, Message } from '@/types'
import AlertFeed from '@/components/AlertFeed'
import IncidentWorkspace from '@/components/IncidentWorkspace'
import CopilotChat from '@/components/CopilotChat'
import { ShieldCheck, Search, AlertTriangle } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { INITIAL_ALERTS, createDemoAlert } from '@/mock/demoAlerts'

export default function Dashboard() {
  const [alerts, setAlerts] = useState<Alert[]>(INITIAL_ALERTS)
  const [selectedAlert, setSelectedAlert] = useState<Alert | null>(null)
  const [severityFilter, setSeverityFilter] = useState('all')
  const [isDemoStreaming, setIsDemoStreaming] = useState(false)
  const [analysisConversation, setAnalysisConversation] = useState<Message[] | null>(null)
  const [analysisConversationId, setAnalysisConversationId] = useState<string | null>(null)

  const handleAnalysisComplete = useCallback((_analysis: unknown, conversation: Message[]) => {
    setAnalysisConversation(conversation)
    setAnalysisConversationId(`analysis-${Date.now()}`)
  }, [])

  const handleSelectAlert = useCallback((alert: Alert | null) => {
    setSelectedAlert(alert)
    setAnalysisConversation(null)
    setAnalysisConversationId(null)
  }, [])

  const openAlerts = alerts.filter((a) => a.status === 'new').length
  const highSeverity = alerts.filter((a) => a.severity === 'high').length
  const triagedToday = alerts.filter((a) => a.status === 'triaged').length

  const handleStartDemoStream = useCallback(() => {
    if (isDemoStreaming) return
    setIsDemoStreaming(true)

    setTimeout(() => {
      const newAlert = createDemoAlert()
      setAlerts((prev) => [newAlert, ...prev])
      setSelectedAlert(newAlert)
      setIsDemoStreaming(false)
    }, 2000)
  }, [isDemoStreaming])

  return (
    <div className="flex flex-col h-screen bg-slate-950 overflow-hidden">
      {/* ── Top Navigation Bar ── */}
      <header className="shrink-0 flex items-center justify-between px-4 py-2.5 bg-slate-900 border-b border-slate-800/80 shadow-md shadow-black/20 z-10">
        <div className="flex items-center gap-3">
          <div className="flex items-center justify-center h-7 w-7 rounded-lg bg-gradient-to-br from-blue-600 to-blue-700 shadow shadow-blue-900/40">
            <ShieldCheck size={14} className="text-white" strokeWidth={2} />
          </div>
          <div className="flex items-baseline gap-2">
            <span className="font-semibold text-slate-100 tracking-tight text-[14px]">
              LogDoc
            </span>
            <Badge
              variant="outline"
              className="text-[9px] px-1.5 py-0 h-4 border-amber-500/40 text-amber-400 bg-amber-500/10"
            >
              Demo Mode
            </Badge>
          </div>

          {/* Metrics */}
          <div className="hidden md:flex items-center gap-1 ml-4">
            <MetricPill label="Open Alerts" value={openAlerts} color="emerald" />
            <MetricPill label="High Severity" value={highSeverity} color="red" />
            <MetricPill label="Triaged Today" value={triagedToday} color="blue" />
          </div>
        </div>

        <div className="flex items-center gap-2">
          {/* Search bar */}
          <div className="relative hidden sm:block">
            <Search
              size={11}
              className="absolute left-2.5 top-1/2 -translate-y-1/2 text-slate-600"
            />
            <input
              type="text"
              placeholder="Search incidents…"
              className="w-44 pl-7 pr-3 py-1.5 text-[11px] bg-slate-800/60 border border-slate-700/60 rounded text-slate-400 placeholder:text-slate-600 focus:outline-none focus:border-blue-500/50 focus:ring-0"
            />
          </div>

          {/* Online indicator */}
          <div className="flex items-center gap-1.5">
            <span className="relative flex h-1.5 w-1.5">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-50" />
              <span className="relative inline-flex rounded-full h-1.5 w-1.5 bg-emerald-500" />
            </span>
            <span className="text-[10px] text-slate-500 hidden sm:inline">Online</span>
          </div>
        </div>
      </header>

      {/* ── 3-Column Layout ── */}
      <div className="flex flex-1 overflow-hidden">
        {/* Left — Alert Feed (20%) */}
        <div className="w-[22%] min-w-[200px] max-w-[280px] flex-shrink-0 overflow-hidden">
          <AlertFeed
            alerts={alerts}
            selectedAlertId={selectedAlert?.id ?? null}
            onSelectAlert={handleSelectAlert}
            onStartDemoStream={handleStartDemoStream}
            isDemoStreaming={isDemoStreaming}
            severityFilter={severityFilter}
            onSeverityFilterChange={setSeverityFilter}
          />
        </div>

        {/* Center — Incident Workspace (50%) */}
        <div className="flex-1 overflow-hidden border-l border-slate-800/80">
          <IncidentWorkspace alert={selectedAlert} onAnalysisComplete={handleAnalysisComplete} />
        </div>

        {/* Right — AI Copilot Chat (28%) */}
        <div className="w-[28%] min-w-[240px] max-w-[360px] flex-shrink-0 overflow-hidden">
          <CopilotChat
            alert={selectedAlert}
            initialMessages={analysisConversation}
            conversationId={analysisConversationId}
          />
        </div>
      </div>
    </div>
  )
}

function MetricPill({
  label,
  value,
  color,
}: {
  label: string
  value: number
  color: 'emerald' | 'red' | 'blue'
}) {
  const colorMap = {
    emerald: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
    red: 'bg-red-500/10 text-red-400 border-red-500/20',
    blue: 'bg-blue-500/10 text-blue-400 border-blue-500/20',
  }
  return (
    <div
      className={`flex items-center gap-1.5 px-2 py-1 rounded border text-[10px] ${colorMap[color]}`}
    >
      {color === 'red' && <AlertTriangle size={9} />}
      <span className="text-slate-500">{label}</span>
      <span className="font-semibold font-mono">{value}</span>
    </div>
  )
}
