import { Sparkles, Loader2, ChevronRight } from 'lucide-react'

const QUICK = [
  'Analyze for missing values, outliers, and key trends',
  'What are the main business insights from this data?',
  'Find correlations and summarize the most important patterns',
  'Full statistical profile with recommendations',
]

export default function PromptBox({ prompt, setPrompt, onAnalyze, disabled, loading }) {
  const ready = !disabled && !loading && prompt.trim().length > 0

  return (
    <div className="card flex flex-col gap-4">
      <div>
        <label className="text-xs font-medium text-slate-300 uppercase tracking-[0.28em] block mb-2">
          Analysis Prompt
        </label>
        <textarea
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          onKeyDown={(e) => { if ((e.metaKey || e.ctrlKey) && e.key === 'Enter' && ready) onAnalyze() }}
          placeholder="What do you want to know about this dataset?"
          rows={4}
          disabled={loading}
          className="input resize-none leading-relaxed"
        />
      </div>

      {/* Quick prompts */}
      <div className="space-y-1">
        {QUICK.map((q) => (
          <button
            key={q}
            onClick={() => setPrompt(q)}
            disabled={loading}
            className="flex items-start gap-1.5 w-full text-left text-xs text-slate-400
              hover:text-white transition-colors py-0.5 disabled:opacity-40"
          >
            <ChevronRight size={10} className="mt-0.5 shrink-0 text-orange-300" />
            <span>{q}</span>
          </button>
        ))}
      </div>

      <button
        onClick={onAnalyze}
        disabled={!ready}
        className="btn-primary w-full justify-center"
      >
        {loading ? <Loader2 size={14} className="animate-spin" /> : <Sparkles size={14} />}
        {loading ? 'Analyzing…' : 'Run Analysis'}
      </button>

      <p className="text-center text-[10px] text-slate-500 font-mono">Cmd/Ctrl + Enter to run</p>
    </div>
  )
}
