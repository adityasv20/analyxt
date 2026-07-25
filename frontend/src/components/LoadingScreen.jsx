import { useEffect, useState } from 'react'

const STEPS = [
  { label: 'Loading dataset',         delay: 0     },
  { label: 'Profiling structure',     delay: 1200  },
  { label: 'Selecting analysis plan', delay: 2800  },
  { label: 'Running analysis tools',  delay: 4500  },
  { label: 'Generating charts',       delay: 7500  },
  { label: 'Writing AI summary',      delay: 11000 },
  { label: 'Assembling report',       delay: 14000 },
]

export default function LoadingScreen() {
  const [active, setActive] = useState(0)

  useEffect(() => {
    const timers = STEPS.map((s, i) => setTimeout(() => setActive(i), s.delay))
    return () => timers.forEach(clearTimeout)
  }, [])

  return (
    <div className="card anim-fade-in py-12 px-8 flex flex-col items-center gap-8">
      {/* Spinner */}
      <div className="relative w-12 h-12">
        <div className="absolute inset-0 rounded-full border border-white/10" />
        <div className="absolute inset-0 rounded-full border border-transparent border-t-cyan-300 animate-spin" />
        <div className="absolute inset-[5px] rounded-full border border-transparent border-t-orange-300/70"
          style={{ animationDuration: '1.8s', animationName: 'spin', animationTimingFunction: 'linear', animationIterationCount: 'infinite' }} />
      </div>

      {/* Steps */}
      <div className="w-full max-w-xs space-y-3">
        {STEPS.map((s, i) => {
          const done   = i < active
          const current = i === active
          return (
            <div key={i} className={`flex items-center gap-3 transition-opacity duration-500
              ${i > active + 1 ? 'opacity-20' : 'opacity-100'}`}>
              {/* Indicator */}
              <div className={`w-4 h-4 rounded-full flex items-center justify-center shrink-0 border transition-all
                ${done ? 'border-green-400/40 bg-green-400/10' : current ? 'border-cyan-300/50 bg-cyan-400/10' : 'border-white/10 bg-transparent'}`}>
                {done && (
                  <svg className="w-2.5 h-2.5 text-green-400" fill="none" viewBox="0 0 12 12" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M2 6l3 3 5-5" />
                  </svg>
                )}
                {current && (
                  <div className="w-1.5 h-1.5 rounded-full bg-cyan-200"
                    style={{ animation: 'pulseDot 1.4s ease-in-out infinite' }} />
                )}
              </div>

              <span className={`text-xs font-mono transition-colors
                ${done ? 'text-slate-500 line-through decoration-slate-600' : current ? 'text-cyan-100' : 'text-slate-500'}`}>
                {s.label}
              </span>
            </div>
          )
        })}
      </div>

      <p className="text-xs text-slate-500 font-mono">Usually under 10 seconds</p>
    </div>
  )
}
