import { useState } from 'react'
import ReactMarkdown from 'react-markdown'
import { Sparkles, ChevronDown, ChevronUp } from 'lucide-react'

export default function AISummary({ summary, wordCount }) {
  const [collapsed, setCollapsed] = useState(false)

  if (!summary) return null

  return (
    <div className="card border-cyan-300/15 anim-fade-up bg-[linear-gradient(180deg,rgba(20,32,46,0.92),rgba(19,12,33,0.9))]">
      {/* Header */}
      <div className="flex items-center gap-2.5 mb-4">
        <div className="p-1.5 rounded-lg bg-cyan-400/12 border border-cyan-300/20">
          <Sparkles size={13} className="text-cyan-200" />
        </div>
        <h3 className="text-sm font-medium text-white">AI Analyst Summary</h3>
        <div className="ml-auto flex items-center gap-2">
          <span className="badge badge-violet">{wordCount} words</span>
          <button
            onClick={() => setCollapsed(c => !c)}
            className="text-slate-500 hover:text-slate-200 transition-colors"
          >
            {collapsed ? <ChevronDown size={14} /> : <ChevronUp size={14} />}
          </button>
        </div>
      </div>

      {!collapsed && (
        <div className="prose anim-fade-in">
          <ReactMarkdown>{summary}</ReactMarkdown>
        </div>
      )}
    </div>
  )
}
