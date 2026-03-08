import { useState, useCallback } from 'react'
import { Alert, Analysis } from '@/types'
import { ScrollArea } from '@/components/ui/scroll-area'
import RawLogViewer from '@/components/RawLogViewer'
import TriageSummary from '@/components/TriageSummary'
import PlaybookPanel from '@/components/PlaybookPanel'
import { AlertTriangle, Shield, Info, Cpu, RotateCcw, CheckCircle2, ArrowUpRight, Database, Globe, ChevronRight } from 'lucide-react'
import { cn } from '@/lib/utils'

interface IncidentWorkspaceProps {
  alert: Alert | null
  /** Called when analysis finishes. Passes the parsed Analysis object. */
  onAnalysisComplete?: (analysis: Analysis) => void
}

const SEVERITY_CONFIG = {
  high: {
    badge: 'bg-red-500/20 text-red-400 border-red-500/30',
    icon: AlertTriangle,
    iconClass: 'text-red-400',
  },
  medium: {
    badge: 'bg-amber-500/20 text-amber-400 border-amber-500/30',
    icon: Shield,
    iconClass: 'text-amber-400',
  },
  low: {
    badge: 'bg-blue-500/20 text-blue-400 border-blue-500/30',
    icon: Info,
    iconClass: 'text-blue-400',
  },
}

const STATUS_BADGE = {
  new: 'bg-emerald-500/15 text-emerald-400 border-emerald-500/25',
  triaged: 'bg-blue-500/15 text-blue-400 border-blue-500/25',
  escalated: 'bg-orange-500/15 text-orange-400 border-orange-500/25',
  resolved: 'bg-slate-500/15 text-slate-400 border-slate-500/25',
}

function StatusPill({ status }: { status: string }) {
  if (!status) return null
  const isKB = status.toLowerCase().includes('knowledge base')
  const isWeb = status.toLowerCase().includes('web')
  return (
    <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-slate-800/90 border border-slate-700/60 w-fit">
      {isKB && <Database size={10} className="text-blue-400 animate-pulse" />}
      {isWeb && <Globe size={10} className="text-emerald-400 animate-pulse" />}
      {!isKB && !isWeb && <ChevronRight size={10} className="text-slate-400 animate-pulse" />}
      <span className="text-[10px] text-slate-400">{status}</span>
    </div>
  )
}

export default function IncidentWorkspace({ alert, onAnalysisComplete }: IncidentWorkspaceProps) {
  const [analysis, setAnalysis] = useState<Analysis | null>(null)
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [analyzeStatus, setAnalyzeStatus] = useState('')
  const [analyzedAlertId, setAnalyzedAlertId] = useState<string | null>(null)

  const currentAnalysis = analyzedAlertId === alert?.id ? analysis : null

  const handleAnalyze = useCallback(async () => {
    if (!alert || isAnalyzing) return
    setIsAnalyzing(true)
    setAnalyzeStatus('')
    setAnalysis(null)
    setAnalyzedAlertId(null)

    // Build the selected_log_data from the alert
    const selectedLogData = {
      raw_log: alert.raw_log,
      source_ip: alert.source_ip,
      dest_ip: alert.dest_ip,
      title: alert.title,
      description: alert.description,
    }

    const userQuery =
      `Analyze the following security incident and provide a complete triage. ` +
      `Classify the activity, identify the MITRE technique, assess confidence, and provide rationale. ` +
      `Then retrieve the appropriate playbook response.`

    const requestBody = {
      user_query: userQuery,
      active_case_id: alert.id,
      active_case_title: alert.title,
      selected_log_data: selectedLogData,
      triage_result: null,
      playbook_result: null,
      conversation_history: [],
    }

    let streamedText = ''
    let finalTriageResult: Analysis['triage_result'] = null
    let finalPlaybookResult: Analysis['playbook_result'] = null
    let finalIntent: string | null = null
    let finalRoutePlan: string[] | null = null

    try {
      const response = await fetch('/api/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(requestBody),
      })

      if (!response.ok) throw new Error(`Server error: ${response.status}`)

      const reader = response.body!.getReader()
      const decoder = new TextDecoder()
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() ?? ''

        for (const line of lines) {
          if (!line.startsWith('data: ')) continue
          const raw = line.slice(6).trim()
          if (!raw) continue

          try {
            const data = JSON.parse(raw)
            if (data.type === 'token') {
              streamedText += data.content
            } else if (data.type === 'status') {
              setAnalyzeStatus(data.content)
            } else if (data.type === 'result') {
              finalTriageResult = data.triage_result ?? null
              finalPlaybookResult = data.playbook_result ?? null
              finalIntent = data.intent ?? null
              finalRoutePlan = data.route_plan ?? null
              console.log('result data', data)
            } else if (data.type === 'done') {
              setAnalyzeStatus('')
              setIsAnalyzing(false)
              const parsed: Analysis = {
                incident_id: alert.id,
                triage_result: finalTriageResult,
                playbook_result: finalPlaybookResult,
                intent: finalIntent,
                route_plan: finalRoutePlan,
                final_response: streamedText,
                raw_response: streamedText,
              }
              console.log('parsed result', parsed)
              setAnalysis(parsed)
              setAnalyzedAlertId(alert.id)
              onAnalysisComplete?.(parsed)
            } else if (data.type === 'error') {
              setAnalyzeStatus('')
              setIsAnalyzing(false)
            }
          } catch {
            // skip malformed
          }
        }
      }
    } catch {
      setIsAnalyzing(false)
      setAnalyzeStatus('')
    }
  }, [alert, isAnalyzing, onAnalysisComplete])

  if (!alert) {
    return (
      <div className="flex flex-col items-center justify-center h-full text-center px-6 bg-slate-950/50">
        <Shield size={28} className="text-slate-700 mb-3" />
        <p className="text-sm text-slate-500 font-medium">No incident selected</p>
        <p className="text-xs text-slate-600 mt-1">
          Select an alert from the feed to begin investigation.
        </p>
      </div>
    )
  }

  const sev = SEVERITY_CONFIG[alert.severity]
  const SevIcon = sev.icon

  return (
    <ScrollArea className="h-full">
      <div className="p-4 space-y-4">
        {/* Incident Header */}
        <div className="rounded-md border border-slate-800/80 bg-slate-900/60 p-4">
          <div className="flex items-start justify-between gap-3 mb-3">
            <div className="flex items-center gap-2 min-w-0">
              <SevIcon size={14} className={cn('shrink-0', sev.iconClass)} />
              <h2 className="text-sm font-semibold text-slate-100 leading-tight truncate">
                {alert.title}
              </h2>
            </div>
            <div className="flex items-center gap-1.5 shrink-0">
              <span
                className={cn(
                  'px-1.5 py-0.5 rounded text-[9px] font-medium border capitalize',
                  sev.badge
                )}
              >
                {alert.severity}
              </span>
              <span
                className={cn(
                  'px-1.5 py-0.5 rounded text-[9px] font-medium border capitalize',
                  STATUS_BADGE[alert.status]
                )}
              >
                {alert.status}
              </span>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-x-4 gap-y-1 mb-4 text-[11px]">
            <div className="flex items-center gap-1.5">
              <span className="text-slate-600 uppercase text-[9px] tracking-widest w-16 shrink-0">
                First Seen
              </span>
              <span className="text-slate-400 font-mono">{alert.timestamp}</span>
            </div>
            <div className="flex items-center gap-1.5">
              <span className="text-slate-600 uppercase text-[9px] tracking-widest w-16 shrink-0">
                Source
              </span>
              <span className="text-slate-400 font-mono">{alert.source_ip}</span>
            </div>
            <div className="flex items-center gap-1.5">
              <span className="text-slate-600 uppercase text-[9px] tracking-widest w-16 shrink-0">
                Destination
              </span>
              <span className="text-slate-400 font-mono">{alert.dest_ip}</span>
            </div>
          </div>

          <p className="text-xs text-slate-400 mb-4">{alert.description}</p>

          {/* Action buttons */}
          <div className="flex items-center gap-2">
            <button
              onClick={handleAnalyze}
              disabled={isAnalyzing}
              className={cn(
                'flex items-center gap-1.5 px-3 py-1.5 rounded text-xs font-medium transition-colors',
                currentAnalysis
                  ? 'bg-slate-700/60 text-slate-300 hover:bg-slate-700 border border-slate-600/50'
                  : 'bg-blue-600 text-white hover:bg-blue-500 disabled:opacity-50 disabled:cursor-not-allowed'
              )}
            >
              {currentAnalysis ? (
                <>
                  <RotateCcw size={12} />
                  Re-run Analysis
                </>
              ) : (
                <>
                  <Cpu size={12} />
                  {isAnalyzing ? 'Analyzing…' : 'Analyze'}
                </>
              )}
            </button>

            <button
              disabled
              className="flex items-center gap-1.5 px-3 py-1.5 rounded text-xs font-medium text-slate-600 border border-slate-800/60 cursor-not-allowed"
            >
              <CheckCircle2 size={12} />
              Mark Resolved
            </button>
            <button
              disabled
              className="flex items-center gap-1.5 px-3 py-1.5 rounded text-xs font-medium text-slate-600 border border-slate-800/60 cursor-not-allowed"
            >
              <ArrowUpRight size={12} />
              Escalate
            </button>
          </div>

          {analyzeStatus && (
            <div className="mt-3">
              <StatusPill status={analyzeStatus} />
            </div>
          )}
        </div>

        {/* Raw Evidence */}
        <RawLogViewer rawLog={alert.raw_log} />

        {/* AI Triage Summary */}
        <div>
          <div className="flex items-center gap-1.5 mb-2 px-0.5">
            <Cpu size={11} className="text-slate-500" />
            <span className="text-[10px] font-semibold text-slate-500 uppercase tracking-widest">
              AI Triage Summary
            </span>
          </div>
          <TriageSummary analysis={currentAnalysis} isLoading={isAnalyzing} />
        </div>

        {/* Playbook Context */}
        {(currentAnalysis || isAnalyzing) && (
          <div>
            <div className="flex items-center gap-1.5 mb-2 px-0.5">
              <span className="text-[10px] font-semibold text-slate-500 uppercase tracking-widest">
                Playbook Context
              </span>
            </div>
            <PlaybookPanel analysis={currentAnalysis} />
          </div>
        )}
      </div>
    </ScrollArea>
  )
}
