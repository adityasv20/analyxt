import { useState } from 'react'
import { ChevronDown, ChevronUp, Search, X, AlertTriangle, CheckCircle, TrendingUp, Info } from 'lucide-react'

function Icon({ label, note }) {
  if ((note || '').includes('High') || (note || '').includes('⚠')) return <AlertTriangle size={12} className="text-amber-400 shrink-0" />
  if ((note || '').includes('None') || (note || '').includes('✅') || (note || '').includes('complete')) return <CheckCircle size={12} className="text-green-400 shrink-0" />
  if ((label || '').toLowerCase().includes('correlat')) return <TrendingUp size={12} className="text-cyan-200 shrink-0" />
  return <Info size={12} className="text-slate-500 shrink-0" />
}

function Row({ item }) {
  const [open, setOpen] = useState(false)
  const isObj = typeof item.value === 'object' && item.value !== null
  const valStr = isObj ? JSON.stringify(item.value) : String(item.value)

  return (
    <div
      className={`border-b border-white/8 last:border-0 py-2.5 px-1 rounded-xl transition-colors
        ${isObj ? 'cursor-pointer hover:bg-white/[0.03]' : ''}`}
      onClick={() => isObj && setOpen(o => !o)}
    >
      <div className="flex items-start gap-2.5">
        <Icon label={item.label} note={item.note} />
        <div className="flex-1 min-w-0">
          <div className="flex items-start justify-between gap-3">
            <span className="text-[11px] font-mono text-cyan-100/80 leading-5 shrink-0 min-w-[180px]">
              {item.label}
            </span>
            <span className={`text-xs flex-1 ${isObj ? 'text-slate-400 font-mono truncate' : 'text-slate-100'}`}>
              {!open ? valStr : ''}
            </span>
            {isObj && (
              <span className="text-slate-500 shrink-0">
                {open ? <ChevronUp size={11} /> : <ChevronDown size={11} />}
              </span>
            )}
          </div>

          {isObj && open && (
            <div className="mt-2 grid grid-cols-3 sm:grid-cols-6 gap-1.5">
              {Object.entries(item.value).map(([k, v]) => (
                <div key={k} className="bg-white/[0.04] rounded-xl p-2 text-center border border-white/8">
                  <div className="text-[9px] text-slate-400 uppercase tracking-wide">{k}</div>
                  <div className="text-xs font-mono text-slate-100 mt-0.5">{v}</div>
                </div>
              ))}
            </div>
          )}

          {item.note && (
            <div className="text-[11px] text-slate-400 mt-0.5">{item.note}</div>
          )}
        </div>
      </div>
    </div>
  )
}

const PAGE = 10

export default function FindingsTable({ findings }) {
  const [q, setQ] = useState('')
  const [expanded, setExpanded] = useState(false)

  if (!findings?.length) return null

  const filtered = findings.filter(f =>
    !q || f.label.toLowerCase().includes(q.toLowerCase()) ||
    String(f.value).toLowerCase().includes(q.toLowerCase())
  )
  const visible = expanded ? filtered : filtered.slice(0, PAGE)
  const more = filtered.length - PAGE

  return (
    <div className="card anim-fade-up">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-xs font-mono text-slate-400 uppercase tracking-[0.28em]">
          Findings · {filtered.length}
        </h3>
        {/* Search */}
        <div className="relative">
          <Search size={11} className="absolute left-2.5 top-1/2 -translate-y-1/2 text-slate-500" />
          <input
            value={q} onChange={e => setQ(e.target.value)}
            placeholder="Filter…"
            className="input text-xs pl-7 pr-7 py-1.5 w-36"
          />
          {q && (
            <button onClick={() => setQ('')}
              className="absolute right-2.5 top-1/2 -translate-y-1/2 text-slate-500 hover:text-slate-200">
              <X size={10} />
            </button>
          )}
        </div>
      </div>

      <div>
        {visible.map((f, i) => <Row key={i} item={f} />)}
        {q && filtered.length === 0 && (
          <p className="text-xs text-slate-500 text-center py-4">No results for "{q}"</p>
        )}
      </div>

      {more > 0 && !expanded && (
        <button onClick={() => setExpanded(true)}
          className="mt-3 w-full flex items-center justify-center gap-1.5 text-xs text-slate-400
            hover:text-white py-2 border border-white/8 hover:border-cyan-300/20 rounded-xl transition-colors">
          <ChevronDown size={11} /> {more} more findings
        </button>
      )}
      {expanded && (
        <button onClick={() => setExpanded(false)}
          className="mt-3 w-full flex items-center justify-center gap-1.5 text-xs text-slate-400
            hover:text-white py-2 border border-white/8 hover:border-cyan-300/20 rounded-xl transition-colors">
          <ChevronUp size={11} /> Show less
        </button>
      )}
    </div>
  )
}
