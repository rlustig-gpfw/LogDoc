export interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
}

export interface ChatState {
  messages: Message[]
  isLoading: boolean
  status: string
}

export interface Alert {
  id: string
  title: string
  timestamp: string
  severity: 'low' | 'medium' | 'high'
  status: 'new' | 'triaged' | 'escalated' | 'resolved'
  source_ip: string
  dest_ip: string
  raw_log: string
  description: string
}

export interface PlaybookSource {
  file: string
}

export interface PlaybookResult {
  playbook_name: string
  match_reason: string
  recommended_actions: string[]
  sources: PlaybookSource[]
}

export interface TriageResult {
  classification: string
  mitre_technique: string
  confidence: string
  rationale: string
}

export interface Analysis {
  incident_id: string
  /** Structured triage output from the log_triage node */
  triage_result: TriageResult | null
  /** Structured playbook output from the playbook_retrieval node */
  playbook_result: PlaybookResult | null
  /** Intent the router identified for this turn */
  intent: string | null
  /** Route the router planned */
  route_plan: string[] | null
  /** Final natural-language response from response_composer */
  final_response: string
  /** Raw full streamed text (for display / debugging) */
  raw_response: string
}

export interface ChatContext {
  incident_id: string
  messages: Message[]
}
