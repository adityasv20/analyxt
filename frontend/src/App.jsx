/**
 * App.jsx — Analyzt root
 */

import { useState } from 'react'
import axios from 'axios'

import UploadZone from './components/UploadZone'
import PromptBox from './components/PromptBox'
import LoadingScreen from './components/LoadingScreen'
import OverviewCards from './components/OverviewCards'
import AISummary from './components/AISummary'
import FindingsTable from './components/FindingsTable'
import ChartGallery from './components/ChartGallery'
import ChatPanel from './components/ChatPanel'
import EmailForm from './components/EmailForm'

import { BarChart3, RefreshCw, MessageSquare, ChevronRight } from 'lucide-react'

const API = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export default function App() {
  const [file, setFile] = useState(null)
  const [uploading, setUploading] = useState(false)
  const [prompt, setPrompt] = useState('')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)
  const [chatOpen, setChatOpen] = useState(true)

  const handleUpload = async (csvFile) => {
    setUploading(true); setError(null); setResult(null)
    const form = new FormData()
    form.append('file', csvFile)
    try {
      const { data } = await axios.post(`${API}/upload`, form, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
      setFile(data.filename)
    } catch (e) {
      setError(e.response?.data?.detail || 'Upload failed — is the backend running?')
    } finally {
      setUploading(false)
    }
  }

  const handleAnalyze = async () => {
    if (!file || !prompt.trim()) return
    setLoading(true); setError(null); setResult(null)
    try {
      const { data } = await axios.post(`${API}/analyze`, {
        filename: file, prompt: prompt.trim(),
      }, {
        timeout: 45000,
      })
      setResult(data)
      setChatOpen(true)
    } catch (e) {
      setError(
        e.code === 'ECONNABORTED'
          ? 'Analysis timed out after 45 seconds. Check the backend logs; the AI provider may be slow or unavailable.'
          : (e.response?.data?.detail || 'Analysis failed — check backend logs')
      )
    } finally {
      setLoading(false)
    }
  }

  const handleReset = () => {
    setFile(null); setPrompt(''); setResult(null); setError(null); setLoading(false)
  }

  return (
    <div className="grain min-h-screen flex flex-col bg-[radial-gradient(circle_at_top_left,_rgba(34,211,238,0.16),_transparent_28%),radial-gradient(circle_at_top_right,_rgba(249,115,22,0.14),_transparent_24%),linear-gradient(180deg,_#07131b_0%,_#0a1420_38%,_#140d22_100%)]">
      <header className="sticky top-0 z-40 border-b border-white/10 bg-slate-950/70 backdrop-blur-xl shrink-0">
        <div className="max-w-[1700px] mx-auto px-6 py-3 flex items-center gap-4">
          <div className="flex items-center gap-2.5">
            <div className="p-1.5 rounded-xl bg-cyan-400/12 border border-cyan-300/20 shadow-[0_10px_30px_rgba(34,211,238,0.12)]">
              <BarChart3 size={16} className="text-cyan-200" />
            </div>
            <span className="font-serif italic text-lg text-white leading-none">Analyzt</span>
          </div>

          {file && (
            <div className="hidden sm:flex items-center gap-2 bg-white/5 border border-white/10 rounded-full px-3 py-1">
              <div className="w-1.5 h-1.5 rounded-full bg-green-400 animate-pulse" />
              <span className="text-[11px] text-slate-300 font-mono truncate max-w-[200px]">{file}</span>
            </div>
          )}

          <div className="ml-auto flex items-center gap-2">
            {result && (
              <>
                <button
                  onClick={() => setChatOpen(o => !o)}
                  className={`btn-ghost text-xs gap-1.5 ${chatOpen ? 'text-cyan-100 border-cyan-300/25 bg-cyan-400/10' : ''}`}
                >
                  <MessageSquare size={11} /> Copilot
                </button>
                <button onClick={handleReset} className="btn-ghost text-xs gap-1.5">
                  <RefreshCw size={11} /> New
                </button>
              </>
            )}
          </div>
        </div>
      </header>

      <div className="flex-1 max-w-[1700px] mx-auto w-full px-6 py-6 flex flex-col min-h-0">
        {!result && !loading && (
          <div className="space-y-8 anim-fade-up">
            <div className="text-center space-y-3 pt-6">
              <p className="text-[11px] font-mono text-cyan-100/70 tracking-[0.35em] uppercase">
                AI · pandas · groq
              </p>
              <h1 className="font-serif italic text-5xl md:text-6xl text-white leading-none">
                Data, understood.
              </h1>
              <p className="text-sm text-slate-300/85 max-w-xl mx-auto leading-relaxed">
                Upload a CSV. Ask a question. Get a full analysis with stronger contrast,
                richer visuals, and flexible AI providers that can fall back when quota is tight.
              </p>
            </div>

            <div className="grid md:grid-cols-2 gap-4 max-w-3xl mx-auto w-full">
              <UploadZone onUpload={handleUpload} uploadedFile={file} uploading={uploading} />
              <PromptBox
                prompt={prompt}
                setPrompt={setPrompt}
                onAnalyze={handleAnalyze}
                disabled={!file || loading}
                loading={loading}
              />
            </div>
          </div>
        )}

        {error && (
          <div className="mt-4 flex items-start gap-2.5 p-3.5 rounded-2xl border border-red-500/25 bg-red-950/20 text-xs text-red-300 max-w-3xl mx-auto w-full shadow-[0_12px_40px_rgba(127,29,29,0.18)]">
            <span className="shrink-0 mt-0.5">⚠</span>
            <div>
              <p className="font-medium text-red-200">Error</p>
              <p className="font-mono mt-0.5 opacity-90">{error}</p>
            </div>
          </div>
        )}

        {loading && (
          <div className="mt-8 max-w-sm mx-auto w-full">
            <LoadingScreen />
          </div>
        )}

        {result && (
          <div className="flex gap-5 flex-1 min-h-0">
            <div className="flex-1 min-w-0 overflow-y-auto space-y-4 pr-1 pb-8">
              <div className="flex items-center justify-between pb-3 border-b border-white/10">
                <div>
                  <h2 className="font-serif italic text-xl text-white">Analysis Complete</h2>
                  <p className="text-[11px] text-slate-400 font-mono mt-0.5">
                    {result.plan?.length} steps · {result.findings?.length} findings · {result.chart_paths?.length} charts
                  </p>
                </div>
                <button onClick={handleReset} className="btn-ghost text-xs gap-1.5">
                  <RefreshCw size={11} /> New Analysis
                </button>
              </div>

              <div className="flex items-start gap-2 px-3 py-2.5 rounded-2xl bg-white/5 border border-white/10 shadow-[inset_0_1px_0_rgba(255,255,255,0.03)]">
                <ChevronRight size={12} className="text-orange-300 mt-0.5 shrink-0" />
                <p className="text-xs text-slate-200 italic">{prompt}</p>
              </div>

              <div className="flex flex-wrap gap-2">
                {result.plan?.map((step, i) => (
                  <span
                    key={step}
                    className={`badge badge text-[10px] border font-mono step-${step}`}
                    style={{ animationDelay: `${i * 40}ms` }}
                  >
                    {step.replace(/_/g, ' ')}
                  </span>
                ))}
              </div>

              <OverviewCards overview={result.dataset_overview} />
              <AISummary summary={result.llm_summary} wordCount={result.llm_summary?.split(' ').length || 0} />
              <FindingsTable findings={result.findings} />
              <ChartGallery paths={result.chart_paths} />
              {result.report_filename && <EmailForm reportFilename={result.report_filename} />}
            </div>

            {chatOpen && (
              <div className="shrink-0 w-[360px] flex flex-col">
                <div className="sticky top-[57px] h-[calc(100vh-73px)]">
                  <ChatPanel filename={file} />
                </div>
              </div>
            )}

            {!chatOpen && (
              <div className="shrink-0 pt-1">
                <button
                  onClick={() => setChatOpen(true)}
                  className="flex flex-col items-center gap-2 p-2.5 rounded-xl border border-white/10 text-slate-500 hover:text-cyan-100 hover:border-cyan-300/30 hover:bg-cyan-400/10 transition-all"
                  title="Open Copilot"
                >
                  <MessageSquare size={15} />
                  <span className="text-[9px] font-mono" style={{ writingMode: 'vertical-rl', textOrientation: 'mixed' }}>
                    Copilot
                  </span>
                </button>
              </div>
            )}
          </div>
        )}
      </div>

      {!result && !loading && (
        <footer className="border-t border-white/8 py-4 shrink-0">
          <div className="max-w-[1700px] mx-auto px-6 flex items-center justify-between">
            <p className="text-[11px] text-slate-500 font-mono">Analyzt v2 · FastAPI + React + Groq</p>
            <p className="text-[11px] text-slate-600">Built by Aditya Velagapudi</p>
          </div>
        </footer>
      )}
    </div>
  )
}
