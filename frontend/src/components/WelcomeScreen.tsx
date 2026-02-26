import { ShieldCheck, Network, AlertTriangle, FileSearch, Globe } from 'lucide-react'

const EXAMPLE_PROMPTS = [
  {
    icon: <FileSearch size={16} className="text-blue-400" />,
    title: 'Triage Zeek Logs',
    description: 'Analyze telemetry for threats',
    prompt:
      'Analyze the following Zeek conn.log snippet for suspicious activity and identify any potential MITRE ATT&CK techniques:\n\n',
  },
  {
    icon: <AlertTriangle size={16} className="text-amber-400" />,
    title: 'Brute Force Response',
    description: 'Get the IR playbook',
    prompt:
      'What is the incident response playbook for a network brute force attack? What immediate steps should I take?',
  },
  {
    icon: <Network size={16} className="text-purple-400" />,
    title: 'Recon Detection',
    description: 'Identify scanning activity',
    prompt:
      'How do I detect and respond to network reconnaissance activity in Zeek logs? What indicators should I look for?',
  },
  {
    icon: <Globe size={16} className="text-emerald-400" />,
    title: 'MITRE Mapping',
    description: 'Map techniques to ATT&CK',
    prompt:
      'What MITRE ATT&CK techniques are associated with DNS tunneling, and how can I detect them in network logs?',
  },
]

interface WelcomeScreenProps {
  onPromptSelect: (prompt: string) => void
}

export default function WelcomeScreen({ onPromptSelect }: WelcomeScreenProps) {
  return (
    <div className="flex flex-col items-center justify-center h-full px-6 py-12 text-center select-none">
      {/* Logo mark */}
      <div className="relative mb-6">
        <div className="absolute inset-0 rounded-2xl bg-blue-500/10 blur-xl scale-150" />
        <div className="relative flex items-center justify-center h-16 w-16 rounded-2xl bg-gradient-to-br from-slate-800 to-slate-900 border border-slate-700/80 shadow-xl shadow-black/40">
          <ShieldCheck size={30} className="text-blue-400" strokeWidth={1.5} />
        </div>
      </div>

      <h1 className="text-2xl font-semibold text-slate-100 mb-1 tracking-tight">
        LogDoc
      </h1>
      <p className="text-sm text-slate-400 mb-8 max-w-xs">
        Agentic SOC triage for Zeek network telemetry. Ask about incidents,
        paste logs, or request playbooks.
      </p>

      {/* Capability pills */}
      <div className="flex flex-wrap justify-center gap-2 mb-10">
        {['Zeek Log Analysis', 'MITRE ATT&CK', 'IR Playbooks', 'Web Search'].map(
          (cap) => (
            <span
              key={cap}
              className="px-3 py-1 text-xs rounded-full bg-slate-800/80 border border-slate-700/60 text-slate-400"
            >
              {cap}
            </span>
          )
        )}
      </div>

      {/* Example prompts */}
      <p className="text-xs text-slate-600 mb-3 uppercase tracking-widest font-medium">
        Try an example
      </p>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 w-full max-w-xl">
        {EXAMPLE_PROMPTS.map((item) => (
          <button
            key={item.title}
            onClick={() => onPromptSelect(item.prompt)}
            className="group flex items-start gap-3 p-4 rounded-xl bg-slate-900/70 border border-slate-800 hover:border-slate-700 hover:bg-slate-800/80 transition-all duration-200 text-left cursor-pointer"
          >
            <div className="mt-0.5 shrink-0 flex items-center justify-center h-7 w-7 rounded-md bg-slate-800 border border-slate-700 group-hover:border-slate-600 transition-colors">
              {item.icon}
            </div>
            <div>
              <p className="text-sm font-medium text-slate-200 group-hover:text-white transition-colors">
                {item.title}
              </p>
              <p className="text-xs text-slate-500 mt-0.5">{item.description}</p>
            </div>
          </button>
        ))}
      </div>
    </div>
  )
}
