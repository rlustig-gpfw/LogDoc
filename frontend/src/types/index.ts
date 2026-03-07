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
  title: string
  source: string
  excerpt: string
  relevance: string
}

export interface Analysis {
  incident_id: string
  classification: string
  mitre_technique: string
  confidence: string
  rationale: string
  recommended_actions: string[]
  playbook_sources: PlaybookSource[]
  raw_response: string
}

export interface ChatContext {
  incident_id: string
  messages: Message[]
}
