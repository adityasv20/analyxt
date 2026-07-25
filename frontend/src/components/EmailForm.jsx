import { useState } from 'react'
import axios from 'axios'
import { Mail, Send, CheckCircle, Loader2, AlertTriangle } from 'lucide-react'

const API = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export default function EmailForm({ reportFilename }) {
  const [email,   setEmail]   = useState('')
  const [status,  setStatus]  = useState('idle')
  const [error,   setError]   = useState(null)

  const send = async () => {
    if (!email.trim() || !/\S+@\S+\.\S+/.test(email)) return
    setStatus('sending'); setError(null)
    try {
      await axios.post(`${API}/email`, {
        to_email: email.trim(),
        report_filename: reportFilename,
        subject: 'Your Analyzt Report',
      })
      setStatus('done')
    } catch (e) {
      setError(e.response?.data?.detail || 'Email failed to send')
      setStatus('error')
    }
  }

  return (
    <div className="card">
      <div className="flex items-center gap-2 mb-4">
        <Mail size={13} className="text-orange-200" />
        <h3 className="text-xs font-mono text-slate-400 uppercase tracking-[0.28em]">Email Report</h3>
      </div>

      {status === 'done' ? (
        <div className="flex items-center gap-2 text-xs text-green-200">
          <CheckCircle size={13} /> Report sent to {email}
        </div>
      ) : (
        <div className="space-y-2">
          <div className="flex gap-2">
            <input
              type="email" value={email} onChange={e => setEmail(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && send()}
              placeholder="recipient@example.com"
              className="input text-xs flex-1"
            />
            <button
              onClick={send}
              disabled={status === 'sending' || !email.trim()}
              className="btn-ghost text-xs shrink-0"
            >
              {status === 'sending'
                ? <Loader2 size={12} className="animate-spin" />
                : <Send size={12} />}
              Send
            </button>
          </div>
          {status === 'error' && error && (
            <div className="flex items-start gap-1.5 text-[11px] text-red-300">
              <AlertTriangle size={11} className="shrink-0 mt-0.5" /> {error}
            </div>
          )}
          <p className="text-[10px] text-slate-500 font-mono">
            Don't see it? Check your spam folder.
          </p>
        </div>
      )}
    </div>
  )
}
