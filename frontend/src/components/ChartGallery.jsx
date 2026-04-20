import { useState, useEffect, useCallback } from 'react'
import { BarChart3, X, ChevronLeft, ChevronRight, ZoomIn } from 'lucide-react'

const API = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const LABELS = {
  hist:    'Distribution',
  corr:    'Correlation Matrix',
  cat:     'Category Breakdown',
  box:     'Box Plot',
  scatter: 'Scatter Plot',
  missing: 'Missing Values',
}

function label(path) {
  const stem = path.split('/').pop().split('_')[0]
  return LABELS[stem] || stem
}

export default function ChartGallery({ paths }) {
  const [lb, setLb] = useState(null)

  const nav = useCallback((e) => {
    if (lb === null) return
    if (e.key === 'Escape') setLb(null)
    if (e.key === 'ArrowRight') setLb(i => (i + 1) % paths.length)
    if (e.key === 'ArrowLeft')  setLb(i => (i - 1 + paths.length) % paths.length)
  }, [lb, paths.length])

  useEffect(() => {
    window.addEventListener('keydown', nav)
    return () => window.removeEventListener('keydown', nav)
  }, [nav])

  useEffect(() => {
    document.body.style.overflow = lb !== null ? 'hidden' : ''
    return () => { document.body.style.overflow = '' }
  }, [lb])

  if (!paths?.length) return null

  return (
    <>
      <div className="card anim-fade-up">
        <div className="flex items-center gap-2 mb-4">
          <BarChart3 size={14} className="text-orange-200" />
          <h3 className="text-xs font-mono text-slate-400 uppercase tracking-[0.28em]">
            Charts · {paths.length}
          </h3>
          <span className="text-xs text-slate-500 ml-auto font-mono">click to expand</span>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-3 xl:grid-cols-4 gap-3">
          {paths.map((p, i) => (
            <div
              key={p}
              className="group relative rounded-2xl overflow-hidden border border-white/10
                cursor-zoom-in hover:border-cyan-300/30 transition-all duration-200 shadow-[0_16px_40px_rgba(0,0,0,0.18)]"
              onClick={() => setLb(i)}
              style={{ animationDelay: `${i * 50}ms` }}
            >
              <img
                src={`${API}${p}`} alt={label(p)}
                className="w-full h-40 object-cover transition-transform duration-300 group-hover:scale-[1.04]"
                loading="lazy"
              />
              <div className="absolute inset-0 bg-black/0 group-hover:bg-slate-950/20 transition-colors
                flex items-center justify-center">
                <ZoomIn size={18} className="text-white opacity-0 group-hover:opacity-100 transition-opacity" />
              </div>
              <div className="absolute bottom-0 left-0 right-0 px-2.5 py-1.5
                bg-gradient-to-t from-slate-950 via-slate-950/75 to-transparent">
                <p className="text-[10px] text-slate-200 font-mono truncate">{label(p)}</p>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Lightbox */}
      {lb !== null && (
        <div
          className="fixed inset-0 z-50 bg-slate-950/90 backdrop-blur-xl flex items-center justify-center p-4"
          onClick={() => setLb(null)}
        >
          <button className="absolute top-4 right-4 p-2 rounded-full bg-white/8 text-slate-300
            hover:text-white transition-colors" onClick={() => setLb(null)}>
            <X size={18} />
          </button>

          {paths.length > 1 && (
            <button className="absolute left-4 top-1/2 -translate-y-1/2 p-2 rounded-full
              bg-white/8 text-slate-300 hover:text-white transition-colors"
              onClick={(e) => { e.stopPropagation(); setLb(i => (i - 1 + paths.length) % paths.length) }}>
              <ChevronLeft size={20} />
            </button>
          )}

          <img
            src={`${API}${paths[lb]}`} alt={label(paths[lb])}
            className="max-w-5xl max-h-[88vh] rounded-xl object-contain"
            onClick={(e) => e.stopPropagation()}
          />

          {paths.length > 1 && (
            <button className="absolute right-4 top-1/2 -translate-y-1/2 p-2 rounded-full
              bg-white/8 text-slate-300 hover:text-white transition-colors"
              onClick={(e) => { e.stopPropagation(); setLb(i => (i + 1) % paths.length) }}>
              <ChevronRight size={20} />
            </button>
          )}

          {/* Counter + dots */}
          <div className="absolute bottom-6 left-1/2 -translate-x-1/2 flex flex-col items-center gap-3">
            <div className="flex gap-1.5">
              {paths.map((_, i) => (
                <button key={i} onClick={(e) => { e.stopPropagation(); setLb(i) }}
                  className={`rounded-full transition-all ${i === lb ? 'w-5 h-1.5 bg-cyan-200' : 'w-1.5 h-1.5 bg-slate-500'}`} />
              ))}
            </div>
            <span className="text-xs text-slate-300 font-mono">{label(paths[lb])}</span>
          </div>
        </div>
      )}
    </>
  )
}
