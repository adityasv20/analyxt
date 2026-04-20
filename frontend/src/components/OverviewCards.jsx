import { AlertTriangle, CheckCircle } from 'lucide-react'

function Stat({ label, value, accent }) {
  const color = accent === 'amber' ? 'text-amber-400'
    : accent === 'red' ? 'text-red-400'
    : accent === 'green' ? 'text-green-400'
    : 'text-white'

  return (
    <div className="card-sm">
      <div className={`font-serif italic text-2xl leading-none ${color}`}>{value}</div>
      <div className="text-[10px] text-slate-400 uppercase tracking-[0.24em] mt-1.5 font-mono">{label}</div>
    </div>
  )
}

export default function OverviewCards({ overview }) {
  if (!overview) return null
  const {
    rows, columns, duplicate_rows, memory_usage_kb,
    missing_values, numeric_columns, categorical_columns,
  } = overview

  const hasMissing = Object.keys(missing_values || {}).length > 0

  return (
    <div className="space-y-4 anim-fade-up">
      {/* Four KPI cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 stagger">
        <Stat label="Rows" value={rows.toLocaleString()} />
        <Stat label="Columns" value={columns} />
        <Stat label="Duplicates" value={duplicate_rows} accent={duplicate_rows > 0 ? 'amber' : 'green'} />
        <Stat label="Memory" value={`${memory_usage_kb} KB`} />
      </div>

      {/* Column type tags */}
      <div className="grid sm:grid-cols-2 gap-3">
        {numeric_columns.length > 0 && (
          <div className="card-sm">
            <p className="text-[10px] text-slate-400 uppercase tracking-[0.24em] font-mono mb-2">
              Numeric · {numeric_columns.length}
            </p>
            <div className="flex flex-wrap gap-1.5">
              {numeric_columns.map(c => (
                <span key={c} className="badge badge-violet">{c}</span>
              ))}
            </div>
          </div>
        )}
        {categorical_columns.length > 0 && (
          <div className="card-sm">
            <p className="text-[10px] text-slate-400 uppercase tracking-[0.24em] font-mono mb-2">
              Categorical · {categorical_columns.length}
            </p>
            <div className="flex flex-wrap gap-1.5">
              {categorical_columns.map(c => (
                <span key={c} className="badge badge-zinc">{c}</span>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Missing values alert */}
      {hasMissing ? (
        <div className="flex items-start gap-2.5 p-3.5 rounded-2xl border border-amber-300/20 bg-amber-300/8 shadow-[0_10px_32px_rgba(245,158,11,0.08)]">
          <AlertTriangle size={14} className="text-amber-400 shrink-0 mt-0.5" />
          <div>
            <p className="text-xs font-medium text-amber-300">Missing values detected</p>
            <div className="flex flex-wrap gap-x-3 mt-1">
              {Object.entries(missing_values).map(([col, n]) => (
                <span key={col} className="text-xs text-amber-200/85 font-mono">
                  {col}: {n} ({Math.round(n / rows * 100)}%)
                </span>
              ))}
            </div>
          </div>
        </div>
      ) : (
        <div className="flex items-center gap-2 p-3 rounded-xl border border-green-400/20 bg-green-400/10 text-xs text-green-200">
          <CheckCircle size={13} className="shrink-0" />
          No missing values — dataset is complete
        </div>
      )}
    </div>
  )
}
