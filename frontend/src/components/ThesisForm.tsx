import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { researchApi } from '../api/research'
import type { RunCreate } from '../types/research'

const LOOKBACKS = [
  { days: 30, label: '30D' },
  { days: 90, label: '90D' },
  { days: 180, label: '6M' },
  { days: 365, label: '1Y' },
]

const DEPTHS = [
  { value: 5, label: '5' },
  { value: 8, label: '8' },
  { value: 12, label: '12' },
]

interface ThesisFormProps {
  initial?: Partial<RunCreate>
  compact?: boolean
}

export function ThesisForm({ initial, compact }: ThesisFormProps) {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const { data: config } = useQuery({ queryKey: ['research-config'], queryFn: researchApi.config })

  const [company, setCompany] = useState(initial?.company ?? '')
  const [thesis, setThesis] = useState(initial?.thesis ?? '')
  const [mode, setMode] = useState(initial?.mode ?? 'auto')
  const [lookback, setLookback] = useState(initial?.lookback_days ?? 90)
  const [depth, setDepth] = useState(initial?.results_per_dimension ?? 8)
  const [showOptions, setShowOptions] = useState(!compact)

  const create = useMutation({
    mutationFn: (data: RunCreate) => researchApi.create(data),
    onSuccess: run => {
      queryClient.invalidateQueries({ queryKey: ['research-runs'] })
      navigate(`/research/${run.id}`)
    },
  })

  const canSubmit = company.trim().length > 0 && thesis.trim().length >= 10 && !create.isPending
  const submit = (overrides?: Partial<RunCreate>) =>
    create.mutate({
      company: company.trim(),
      thesis: thesis.trim(),
      mode,
      lookback_days: lookback,
      results_per_dimension: depth,
      ...overrides,
    })

  const selectedMode = config?.modes.find(m => m.value === mode)

  return (
    <div className="panel p-5">
      <div className="eyebrow mb-4">Research thesis</div>

      <div className="grid grid-cols-1 md:grid-cols-[180px_1fr] gap-4">
        <div>
          <label className="eyebrow block mb-1.5">Company</label>
          <input
            className="field font-medium"
            placeholder="PLTR or Palantir"
            value={company}
            onChange={e => setCompany(e.target.value)}
          />
        </div>
        <div>
          <label className="eyebrow block mb-1.5">Investment thesis</label>
          <textarea
            className="field resize-y min-h-[64px] leading-relaxed"
            rows={2}
            placeholder="High switching costs across defense, intelligence, and large corporations create entrenched, non-cancelable performance obligations."
            value={thesis}
            onChange={e => setThesis(e.target.value)}
          />
        </div>
      </div>

      {showOptions && config && (
        <div className="mt-5 space-y-4">
          <div>
            <div className="flex items-baseline justify-between mb-2">
              <label className="eyebrow">Exa search mode</label>
              {selectedMode && (
                <span className="text-xs text-stone-500">
                  Sent as <code className="font-mono text-stone-700">type: "{selectedMode.value}"</code> on every search
                </span>
              )}
            </div>
            <div className="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-6 gap-2">
              {config.modes.map(m => (
                <button
                  key={m.value}
                  type="button"
                  onClick={() => setMode(m.value)}
                  className={`text-left px-3 py-2.5 border rounded-sm transition-colors ${
                    mode === m.value
                      ? 'border-amber-600 bg-amber-50'
                      : 'border-stone-200 bg-white hover:border-stone-400'
                  }`}
                >
                  <div className="flex items-baseline justify-between gap-2">
                    <span className={`text-sm font-semibold ${mode === m.value ? 'text-amber-900' : 'text-stone-900'}`}>
                      {m.label}
                    </span>
                    <span className="font-mono text-[10px] text-stone-400">{m.latency}</span>
                  </div>
                  <div className="text-xs text-stone-500 mt-0.5 leading-snug">{m.description}</div>
                </button>
              ))}
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-x-8 gap-y-3">
            <div className="flex items-center gap-2">
              <span className="eyebrow">Lookback</span>
              {LOOKBACKS.map(l => (
                <button
                  key={l.days}
                  type="button"
                  className={lookback === l.days ? 'toggle-active' : 'toggle'}
                  onClick={() => setLookback(l.days)}
                >
                  {l.label}
                </button>
              ))}
            </div>
            <div className="flex items-center gap-2">
              <span className="eyebrow">Sources per dimension</span>
              {DEPTHS.map(d => (
                <button
                  key={d.value}
                  type="button"
                  className={depth === d.value ? 'toggle-active' : 'toggle'}
                  onClick={() => setDepth(d.value)}
                >
                  {d.label}
                </button>
              ))}
            </div>
          </div>
        </div>
      )}

      <div className="mt-5 flex flex-wrap items-center gap-3">
        <button className="btn-accent" disabled={!canSubmit} onClick={() => submit()}>
          {create.isPending ? 'Starting…' : 'Research thesis'}
        </button>
        <button
          className="btn-outline"
          disabled={!canSubmit}
          onClick={() => submit({ mode: 'instant', results_per_dimension: 5 })}
        >
          Quick scan
        </button>
        <span className="eyebrow normal-case tracking-normal font-sans text-xs text-stone-500">
          {showOptions
            ? `Runs 7 live Exa searches: ecosystem map + ${config?.dimensions.length ?? 6} thesis dimensions. Quick scan forces instant mode.`
            : (
              <button className="link-accent" onClick={() => setShowOptions(true)}>
                Change search mode & options
              </button>
            )}
        </span>
      </div>

      {create.isError && (
        <p className="mt-3 text-sm text-red-700 bg-red-50 border border-red-200 rounded-sm px-3 py-2">
          {(create.error as Error).message}
        </p>
      )}
    </div>
  )
}
