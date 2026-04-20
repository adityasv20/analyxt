import { useRef, useState } from 'react'
import { Upload, FileCheck, RotateCcw } from 'lucide-react'

export default function UploadZone({ onUpload, uploadedFile, uploading }) {
  const inputRef = useRef()
  const [dragging, setDragging] = useState(false)
  const [invalid, setInvalid] = useState(false)

  const handle = (file) => {
    if (!file) return
    if (!file.name.endsWith('.csv')) {
      setInvalid(true)
      setTimeout(() => setInvalid(false), 2000)
      return
    }
    onUpload(file)
  }

  const onDrop = (e) => {
    e.preventDefault()
    setDragging(false)
    handle(e.dataTransfer.files[0])
  }

  const border = invalid
    ? 'border-red-400/50 bg-red-500/10'
    : dragging
    ? 'border-cyan-300/60 bg-cyan-400/10'
    : uploadedFile
    ? 'border-emerald-300/40 bg-emerald-400/10'
    : 'border-white/12 hover:border-cyan-300/25 bg-white/[0.025]'

  return (
    <div
      className={`relative flex flex-col items-center justify-center gap-3 rounded-xl border-2
        border-dashed cursor-pointer transition-all duration-200 py-10 px-6 ${border}`}
      onClick={() => !uploading && inputRef.current.click()}
      onDragOver={(e) => { e.preventDefault(); setDragging(true) }}
      onDragLeave={() => setDragging(false)}
      onDrop={onDrop}
    >
      <input
        ref={inputRef} type="file" accept=".csv"
        className="hidden" onChange={(e) => handle(e.target.files[0])}
      />

      {uploading ? (
        <>
          <div className="w-8 h-8 rounded-full border-2 border-cyan-300 border-t-transparent animate-spin" />
          <p className="text-sm text-slate-200">Uploading…</p>
        </>
      ) : uploadedFile ? (
        <>
          <FileCheck size={28} className="text-green-400" />
          <div className="text-center">
            <p className="text-sm font-medium text-emerald-200">{uploadedFile}</p>
            <button
              className="text-xs text-slate-400 hover:text-white mt-1 flex items-center gap-1 mx-auto"
              onClick={(e) => { e.stopPropagation(); inputRef.current.click() }}
            >
              <RotateCcw size={10} /> replace
            </button>
          </div>
        </>
      ) : invalid ? (
        <>
          <Upload size={26} className="text-red-400" />
          <p className="text-sm text-red-400">CSV files only</p>
        </>
      ) : (
        <>
          <div className={`p-2.5 rounded-xl border transition-colors
            ${dragging ? 'border-cyan-300/40 bg-cyan-400/10' : 'border-white/10 bg-white/[0.04]'}`}>
            <Upload size={22} className={dragging ? 'text-cyan-200' : 'text-orange-200'} />
          </div>
          <div className="text-center">
            <p className="text-sm font-medium text-white">
              {dragging ? 'Drop it' : 'Drop a CSV'}
            </p>
            <p className="text-xs text-slate-400 mt-0.5">or click to browse</p>
          </div>
        </>
      )}
    </div>
  )
}
