import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism'
import { Avatar, AvatarFallback } from '@/components/ui/avatar'
import { Message } from '@/types'
import { formatTime } from '@/lib/utils'
import { ShieldCheck, User } from 'lucide-react'

interface MessageBubbleProps {
  message: Message
  isStreaming?: boolean
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
const MarkdownComponents: any = {
  h1: ({ children }: { children: React.ReactNode }) => (
    <h1 className="text-xl font-bold text-slate-100 mb-3 mt-5 first:mt-0 pb-1 border-b border-slate-700">
      {children}
    </h1>
  ),
  h2: ({ children }: { children: React.ReactNode }) => (
    <h2 className="text-lg font-bold text-slate-100 mb-2 mt-4 first:mt-0">
      {children}
    </h2>
  ),
  h3: ({ children }: { children: React.ReactNode }) => (
    <h3 className="text-base font-semibold text-blue-300 mb-2 mt-3 first:mt-0">
      {children}
    </h3>
  ),
  h4: ({ children }: { children: React.ReactNode }) => (
    <h4 className="text-sm font-semibold text-slate-200 mb-1.5 mt-3 first:mt-0 uppercase tracking-wide">
      {children}
    </h4>
  ),
  p: ({ children }: { children: React.ReactNode }) => (
    <p className="text-slate-200 mb-3 last:mb-0 leading-relaxed">{children}</p>
  ),
  ul: ({ children }: { children: React.ReactNode }) => (
    <ul className="list-none text-slate-200 mb-3 space-y-1.5 ml-1">{children}</ul>
  ),
  ol: ({ children }: { children: React.ReactNode }) => (
    <ol className="list-decimal list-inside text-slate-200 mb-3 space-y-1.5 ml-1">
      {children}
    </ol>
  ),
  li: ({ children }: { children: React.ReactNode }) => (
    <li className="text-slate-200 flex gap-2 items-start">
      <span className="text-blue-400 mt-1 shrink-0">▸</span>
      <span>{children}</span>
    </li>
  ),
  strong: ({ children }: { children: React.ReactNode }) => (
    <strong className="font-semibold text-slate-100">{children}</strong>
  ),
  em: ({ children }: { children: React.ReactNode }) => (
    <em className="italic text-slate-300">{children}</em>
  ),
  blockquote: ({ children }: { children: React.ReactNode }) => (
    <blockquote className="border-l-2 border-blue-500 pl-4 my-3 text-slate-400 italic bg-slate-900/50 py-2 rounded-r">
      {children}
    </blockquote>
  ),
  table: ({ children }: { children: React.ReactNode }) => (
    <div className="overflow-x-auto my-3 rounded border border-slate-700">
      <table className="w-full text-sm text-slate-200 border-collapse">
        {children}
      </table>
    </div>
  ),
  thead: ({ children }: { children: React.ReactNode }) => (
    <thead className="bg-slate-800">{children}</thead>
  ),
  th: ({ children }: { children: React.ReactNode }) => (
    <th className="px-4 py-2.5 text-left font-semibold text-slate-100 border-b border-slate-700 text-xs uppercase tracking-wide">
      {children}
    </th>
  ),
  td: ({ children }: { children: React.ReactNode }) => (
    <td className="px-4 py-2.5 border-b border-slate-800 text-slate-300">
      {children}
    </td>
  ),
  hr: () => <hr className="my-4 border-slate-700" />,
  a: ({
    href,
    children,
  }: {
    href?: string
    children: React.ReactNode
  }) => (
    <a
      href={href}
      className="text-blue-400 hover:text-blue-300 underline underline-offset-2 transition-colors"
      target="_blank"
      rel="noopener noreferrer"
    >
      {children}
    </a>
  ),
  code: ({
    inline,
    className,
    children,
    ...props
  }: {
    inline?: boolean
    className?: string
    children: React.ReactNode
  }) => {
    const match = /language-(\w+)/.exec(className || '')
    return !inline && match ? (
      <SyntaxHighlighter
        style={vscDarkPlus}
        language={match[1]}
        PreTag="div"
        className="!rounded-md !my-3 !text-sm !bg-slate-900 border border-slate-700"
        customStyle={{ margin: '12px 0', borderRadius: '6px' }}
        {...props}
      >
        {String(children).replace(/\n$/, '')}
      </SyntaxHighlighter>
    ) : (
      <code
        className="bg-slate-800 text-blue-300 px-1.5 py-0.5 rounded text-[0.85em] font-mono border border-slate-700"
        {...props}
      >
        {children}
      </code>
    )
  },
  pre: ({ children }: { children: React.ReactNode }) => (
    <div className="not-prose">{children}</div>
  ),
}

export default function MessageBubble({ message, isStreaming }: MessageBubbleProps) {
  const isUser = message.role === 'user'

  return (
    <div
      className={`flex gap-3 animate-slide-up ${isUser ? 'flex-row-reverse' : 'flex-row'}`}
    >
      {/* Avatar */}
      <div className="shrink-0 mt-0.5">
        {isUser ? (
          <Avatar className="h-8 w-8 ring-1 ring-slate-700">
            <AvatarFallback className="bg-blue-700 text-white">
              <User size={14} />
            </AvatarFallback>
          </Avatar>
        ) : (
          <Avatar className="h-8 w-8 ring-1 ring-blue-900/60">
            <AvatarFallback className="bg-slate-800 text-blue-400">
              <ShieldCheck size={14} />
            </AvatarFallback>
          </Avatar>
        )}
      </div>

      {/* Bubble */}
      <div className={`flex flex-col gap-1 max-w-[82%] ${isUser ? 'items-end' : 'items-start'}`}>
        <div
          className={`
            rounded-2xl px-4 py-3 text-sm leading-relaxed
            ${isUser
              ? 'bg-blue-600 text-white rounded-tr-sm shadow-lg shadow-blue-900/20'
              : 'bg-slate-800/90 text-slate-200 rounded-tl-sm border border-slate-700/60 shadow-lg shadow-black/20'
            }
          `}
        >
          {isUser ? (
            <p className="whitespace-pre-wrap break-words">{message.content}</p>
          ) : message.content ? (
            <div className="prose prose-invert max-w-none">
              <ReactMarkdown
                remarkPlugins={[remarkGfm]}
                components={MarkdownComponents}
              >
                {message.content}
              </ReactMarkdown>
              {isStreaming && (
                <span className="inline-block w-0.5 h-4 bg-blue-400 ml-0.5 animate-pulse align-text-bottom" />
              )}
            </div>
          ) : (
            <div className="flex items-center gap-1.5 py-0.5">
              <span className="typing-dot" />
              <span className="typing-dot" />
              <span className="typing-dot" />
            </div>
          )}
        </div>

        <span className="text-[10px] text-slate-600 px-1">
          {formatTime(message.timestamp)}
        </span>
      </div>
    </div>
  )
}
