import { useState } from 'react'
import { Check, ChevronDown, ChevronRight, Loader2, X } from 'lucide-react'
import type { TraceStep } from '../hooks/useResearchStream'
import { faviconUrl, formatCost, formatMs } from '../lib/format'

function StepIcon({ status }: { status: TraceStep['status'] }) {
  if (status === 'running') return <Loader2 className="h-3.5 w-3.5 animate-spin text-amber-600" />
  if (status === 'done') return <Check className="h-3.5 w-3.5 text-emerald-600" />
  if (status === 'error') return <X className="h-3.5 w-3.5 text-red-600" />
  return <span className="h-1.5 w-1.5 rounded-full bg-stone-300" />
}

function StepRow({ step, index }: { step: TraceStep; index: number }) {
  const [open, setOpen] = useState(false)
  const [showRequest, setShowRequest] = useState(false)
  const domains = Array.from(new Set(step.sources.map(s => s.domain).filter(Boolean)))

  return (
    <li className="relative pl-8 pb-4 last:pb-0">
      <span className="absolute left-[11px] top-6 bottom-0 w-px bg-stone-200" />
      <span className="absolute left-0 top-0.5 h-6 w-6 rounded-full border border-stone-200 bg-white flex items-center justify-center">
        <StepIcon status={step.status} />
      </span>

      <div className="flex items-baseline gap-2 flex-wrap">
        <span className="font-mono text-[10px] text-stone-400">{String(index + 1).padStart(2, '0')}</span>
        <span className={`text-sm font-semibold ${step.status === 'queued' ? 'text-stone-400' : 'text-stone-900'}`}>
          {step.label}
        </span>
        {step.searchType && <span className="mono-tag border-stone-200 text-stone-500">type: {step.searchType}</span>}
        <span className="ml-auto flex items-center gap-3 font-mono text-[10.5px] text-stone-500">
          {step.elapsedMs != null && <span>{formatMs(step.elapsedMs)}</span>}
          {step.cost != null && <span>{formatCost(step.cost)}</span>}
        </span>
      </div>

      {step.status === 'queued' && <p className="text-xs text-stone-400 mt-1">Queued</p>}

      {step.query && (
        <p className="mt-1 text-xs text-stone-600">
          <span className="font-mono text-stone-400">query › </span>
          {step.query}
        </p>
      )}

      {step.status === 'running' && step.sources.length === 0 && (
        <p className="mt-1.5 text-xs text-amber-700">
          Exa is searching the web and synthesizing grounded signals…
        </p>
      )}

      {domains.length > 0 && (
        <div className="mt-2 flex items-center gap-1.5 flex-wrap">
          <span className="font-mono text-[10.5px] text-stone-400">
            read {step.sources.length} source{step.sources.length !== 1 ? 's' : ''} ›
          </span>
          {domains.slice(0, 8).map(d => (
            <span key={d} className="inline-flex items-center gap-1 text-[11px] text-stone-600 bg-stone-50 border border-stone-200 rounded-sm px-1.5 py-0.5">
              <img src={faviconUrl(d)} alt="" className="h-3 w-3" loading="lazy" />
              {d}
            </span>
          ))}
          {domains.length > 8 && <span className="text-[11px] text-stone-400">+{domains.length - 8}</span>}
        </div>
      )}

      {step.summary && (
        <p className="mt-1.5 font-mono text-[10.5px] uppercase tracking-[0.1em] text-emerald-700">› {step.summary}</p>
      )}
      {step.error && <p className="mt-1.5 text-xs text-red-700">{step.error}</p>}

      {(step.sources.length > 0 || step.request) && (
        <div className="mt-1.5 flex gap-4">
          {step.sources.length > 0 && (
            <button className="link-accent" onClick={() => setOpen(!open)}>
              {open ? 'Hide sources' : 'Show sources'}
            </button>
          )}
          {step.request && (
            <button className="link-accent" onClick={() => setShowRequest(!showRequest)}>
              {showRequest ? 'Hide request' : 'Exa request'}
            </button>
          )}
          {step.requestId && <span className="font-mono text-[10px] text-stone-400 self-center">id {step.requestId}</span>}
        </div>
      )}

      {open && (
        <ol className="mt-2 space-y-1 border-l-2 border-stone-100 pl-3">
          {step.sources.map(s => (
            <li key={s.url} className="text-xs">
              <a href={s.url} target="_blank" rel="noreferrer" className="text-stone-800 hover:text-amber-800 hover:underline">
                {s.title || s.url}
              </a>
              <span className="ml-2 font-mono text-[10px] text-stone-400">{s.domain}</span>
            </li>
          ))}
        </ol>
      )}

      {showRequest && step.request && (
        <pre className="mt-2 max-h-72 overflow-auto bg-stone-900 text-stone-100 text-[11px] leading-relaxed rounded-sm p-3">
          {`POST https://api.exa.ai/search\n${JSON.stringify(step.request, null, 2)}`}
        </pre>
      )}
    </li>
  )
}

interface ResearchTraceProps {
  steps: TraceStep[]
  running: boolean
}

export function ResearchTrace({ steps, running }: ResearchTraceProps) {
  const [manualOpen, setManualOpen] = useState<boolean | null>(null)
  const open = manualOpen ?? running
  const done = steps.filter(s => s.status === 'done').length
  const sourceCount = steps.reduce((n, s) => n + s.sources.length, 0)

  return (
    <div className="panel">
      <button
        className="w-full flex items-center gap-3 px-5 py-3.5 text-left"
        onClick={() => setManualOpen(!open)}
      >
        {open ? <ChevronDown className="h-4 w-4 text-stone-400" /> : <ChevronRight className="h-4 w-4 text-stone-400" />}
        <span className="eyebrow text-stone-700">Exa research trace</span>
        <span className="font-mono text-[10.5px] text-stone-500">
          {done}/{steps.length || 7} steps · {sourceCount} sources read
        </span>
        {running && (
          <span className="ml-auto flex items-center gap-1.5 font-mono text-[10.5px] uppercase tracking-[0.1em] text-amber-700">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-amber-400 opacity-75" />
              <span className="relative inline-flex rounded-full h-2 w-2 bg-amber-500" />
            </span>
            Live
          </span>
        )}
      </button>
      {open && (
        <div className="px-5 pb-5 pt-1 border-t border-stone-100">
          {steps.length === 0 ? (
            <p className="text-xs text-stone-500 py-3">Connecting to the research run…</p>
          ) : (
            <ol className="pt-3">
              {steps.map((s, i) => <StepRow key={s.key} step={s} index={i} />)}
            </ol>
          )}
        </div>
      )}
    </div>
  )
}
