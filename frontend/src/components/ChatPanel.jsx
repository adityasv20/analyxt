import { useState, useRef, useEffect } from 'react'
import axios from 'axios'
import ReactMarkdown from 'react-markdown'
import { Send, Loader2, MessageSquare, Database, Sparkles, Bot, User, X, Trash2 } from 'lucide-react'

const API = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const SUGGESTIONS = [
  'What are the key statistics?',
  'Which rows have the highest values?',
  'Are there strong correlations?',
  'Show me the top 5 records',
  'What columns have missing data?',
  'What is the data distribution like?',
]

function MethodPill({ method }) {
  return method === 'pandas'
    ? <span className="badge badge-green" style={{ fontSize: '9px' }}><Database size={7} /> computed</span>
    : <span className="badge badge-violet" style={{ fontSize: '9px' }}><Sparkles size={7} /> ai</span>
}

function Bubble({ msg }) {
  const isUser = msg.role === 'user'

  return (
    <div className={`flex items-start gap-2 ${isUser ? 'flex-row-reverse' : ''}`}>
      {/* Avatar */}
      <div className={`w-5 h-5 rounded-full flex items-center justify-center shrink-0 mt-0.5 border
        ${isUser
          ? 'bg-cyan-400/15 border-cyan-300/25 shadow-[0_0_24px_rgba(34,211,238,0.08)]'
          : 'bg-white/8 border-white/10'}`}>
        {isUser
          ? <User size={10} className="text-cyan-200" />
          : <Bot size={10} className="text-orange-200" />}
      </div>

      {/* Content */}
      <div className={`max-w-[88%] ${isUser ? 'items-end' : 'items-start'} flex flex-col gap-1`}>
        {msg.method && <MethodPill method={msg.method} />}
        <div className={`rounded-xl px-3 py-2 text-xs leading-relaxed
          ${isUser
            ? 'bg-cyan-400/14 border border-cyan-300/20 text-slate-100 rounded-tr-sm'
            : 'bg-slate-900/65 border border-white/10 rounded-tl-sm shadow-[inset_0_1px_0_rgba(255,255,255,0.03)]'}`}>
          {isUser
            ? <span className="text-slate-100">{msg.content}</span>
            : <div className="chat-prose"><ReactMarkdown>{msg.content}</ReactMarkdown></div>
          }
        </div>
      </div>
    </div>
  )
}

function TypingDots() {
  return (
    <div className="flex items-start gap-2">
      <div className="w-5 h-5 rounded-full bg-white/8 border border-white/10
        flex items-center justify-center shrink-0">
        <Bot size={10} className="text-orange-200" />
      </div>
      <div className="bg-slate-900/65 border border-white/10 rounded-xl rounded-tl-sm px-3.5 py-2.5">
        <div className="flex gap-1 items-center">
          {[0, 150, 300].map(d => (
            <div key={d} className="w-1 h-1 rounded-full bg-cyan-200/80"
              style={{ animation: `pulseDot 1.4s ease-in-out ${d}ms infinite` }} />
          ))}
        </div>
      </div>
    </div>
  )
}

export default function ChatPanel({ filename }) {
  const [messages, setMessages] = useState([])
  const [input, setInput]       = useState('')
  const [loading, setLoading]   = useState(false)
  const [error, setError]       = useState(null)
  const bottomRef = useRef()
  const inputRef  = useRef()

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, loading])

  const send = async (text) => {
    const q = (text || input).trim()
    if (!q || loading || !filename) return

    setInput('')
    setError(null)
    const userMsg = { role: 'user', content: q }
    setMessages(prev => [...prev, userMsg])
    setLoading(true)

    try {
      const history = messages.map(m => ({ role: m.role, content: m.content }))
      const { data } = await axios.post(`${API}/chat`, { filename, question: q, history })
      setMessages(prev => [...prev, {
        role: 'assistant', content: data.answer, method: data.method
      }])
    } catch (e) {
      setError(e.response?.data?.detail || 'Chat failed')
      setMessages(prev => prev.slice(0, -1))
    } finally {
      setLoading(false)
    }
  }

  const isEmpty = messages.length === 0

  return (
    <div className="flex flex-col h-full rounded-[28px] border border-white/10
      bg-[linear-gradient(180deg,rgba(8,18,28,0.9),rgba(16,12,28,0.78))] overflow-hidden anim-slide-in shadow-[0_24px_60px_rgba(0,0,0,0.28)]">

      {/* Header */}
      <div className="flex items-center gap-2.5 px-4 py-3 border-b border-white/10 shrink-0 bg-white/[0.03]">
        <div className="p-1.5 rounded-lg bg-cyan-400/12 border border-cyan-300/20">
          <MessageSquare size={13} className="text-cyan-200" />
        </div>
        <div className="flex-1 min-w-0">
          <p className="text-xs font-medium text-white leading-none">Data Copilot</p>
          <p className="text-[10px] text-slate-400 mt-0.5 font-mono truncate leading-none">
            {filename ? filename : 'no dataset loaded'}
          </p>
        </div>
        <div className="flex items-center gap-2">
          {messages.length > 0 && (
            <button onClick={() => setMessages([])}
              className="text-slate-500 hover:text-slate-200 transition-colors"
              title="Clear chat">
              <Trash2 size={12} />
            </button>
          )}
          <div className={`w-1.5 h-1.5 rounded-full ${filename ? 'bg-green-400' : 'bg-zinc-600'}`} />
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-4 py-4 space-y-3 min-h-0">
        {isEmpty ? (
          <div className="h-full flex flex-col justify-center">
            <div className="text-center mb-5">
              <div className="inline-flex p-3 rounded-xl bg-cyan-400/10 border border-cyan-300/15 mb-3">
                <MessageSquare size={20} className="text-cyan-200" />
              </div>
              <p className="text-xs font-medium text-slate-200">Ask anything about your data</p>
              <p className="text-[11px] text-slate-400 mt-1">
                {filename ? 'Try a question below' : 'Run an analysis first'}
              </p>
            </div>
            {filename && (
              <div className="space-y-1.5">
                {SUGGESTIONS.map(s => (
                  <button key={s} onClick={() => send(s)} disabled={loading}
                    className="w-full text-left text-[11px] text-slate-300/75 hover:text-white
                      bg-white/[0.03] hover:bg-cyan-400/10 border border-white/8
                      hover:border-cyan-300/20 px-3 py-2 rounded-xl transition-all
                      disabled:opacity-40 font-mono">
                    {s}
                  </button>
                ))}
              </div>
            )}
          </div>
        ) : (
          <>
            {messages.map((m, i) => <Bubble key={i} msg={m} />)}
            {loading && <TypingDots />}
            {error && (
              <div className="flex items-start gap-2 p-3 rounded-lg border border-red-500/25
                bg-red-950/20 text-[11px] text-red-300">
                <X size={11} className="shrink-0 mt-0.5" /> {error}
              </div>
            )}
          </>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <div className="px-4 py-3 border-t border-white/10 shrink-0 bg-white/[0.02]">
        <div className="flex gap-2 items-end">
          <textarea
            ref={inputRef}
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send() } }}
            placeholder={filename ? 'Ask about your data…' : 'Upload a dataset first'}
            disabled={!filename || loading}
            rows={1}
            className="input text-xs resize-none min-h-[36px] max-h-[100px] leading-relaxed py-2"
            style={{ overflowY: 'auto' }}
          />
          <button
            onClick={() => send()}
            disabled={!filename || !input.trim() || loading}
            className="btn-primary p-2.5 shrink-0"
            style={{ padding: '9px' }}
          >
            {loading
              ? <Loader2 size={14} className="animate-spin" />
              : <Send size={14} />
            }
          </button>
        </div>
        <p className="text-[9px] text-slate-500 text-center mt-1.5 font-mono">
          Enter · Shift+Enter for newline
        </p>
      </div>
    </div>
  )
}
