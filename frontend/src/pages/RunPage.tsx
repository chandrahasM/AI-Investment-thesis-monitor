import { useEffect, useMemo, useState } from 'react'
import { useParams } from 'react-router-dom'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { researchApi } from '../api/research'
import { useResearchStream } from '../hooks/useResearchStream'
import { ThesisForm } from '../components/ThesisForm'
import { ResearchTrace } from '../components/ResearchTrace'
import { SignalCard } from '../components/SignalCard'
import { AgentPanel, EcosystemPanel, PeoplePanel, StatusPanel } from '../components/SidePanels'
import { ageInDays } from '../lib/format'
import type { ResearchSignal } from '../types/research'

const IMPACT_FILTERS = ['all', 'high', 'medium', 'low'] as const
const DIRECTION_FILTERS = [
  { value: 'all', label: 'All' },
  { value: 'positive', label: 'Positive' },
  { value: 'negative', label: 'Negative' },
  { value: 'neutral', label: 'Neutral' },
]
const PUBLISHED_FILTERS = [
  { value: Infinity, label: 'Any' },
  { value: 1, label: '24H' },
  { value: 7, label: '7D' },
  { value: 30, label: '30D' },
  { value: 90, label: '90D' },
]
const IMPACT_RANK = { high: 0, medium: 1, low: 2 }

function sortSignals(signals: ResearchSignal[]) {
  return [...signals].sort((a, b) =>
    IMPACT_RANK[a.impact] - IMPACT_RANK[b.impact] || ageInDays(a.published_date) - ageInDays(b.published_date),
  )
}

export function RunPage() {
  const { id = '' } = useParams()
  const queryClient = useQueryClient()
  const stream = useResearchStream(id)
  const { data: run, error } = useQuery({ queryKey: ['research-run', id], queryFn: () => researchApi.get(id) })

  const [impact, setImpact] = useState<(typeof IMPACT_FILTERS)[number]>('all')
  const [dimension, setDimension] = useState('all')
  const [direction, setDirection] = useState('all')
  const [published, setPublished] = useState(Infinity)

  useEffect(() => {
    if (stream.connection === 'ended') {
      queryClient.invalidateQueries({ queryKey: ['research-run', id] })
      queryClient.invalidateQueries({ queryKey: ['research-runs'] })
    }
  }, [stream.connection, id, queryClient])

  const running = stream.connection !== 'ended' && stream.connection !== 'lost' && stream.status !== 'completed' && stream.status !== 'failed'
  const signals = useMemo(() => (running ? stream.signals : sortSignals(stream.signals)), [running, stream.signals])

  const dimensions = useMemo(
    () => stream.steps.filter(s => s.key !== 'ecosystem').map(s => ({ key: s.key, label: s.label })),
    [stream.steps],
  )

  const filtered = signals.filter(s =>
    (impact === 'all' || s.impact === impact) &&
    (dimension === 'all' || s.dimension === dimension) &&
    (direction === 'all' || s.direction === direction) &&
    ageInDays(s.published_date) <= published,
  )

  if (error) {
    return <p className="text-sm text-red-700">Could not load this research run: {(error as Error).message}</p>
  }
  if (!run) return <p className="text-sm text-stone-500">Loading research run…</p>

  const failedWithoutTrace = run.status === 'failed' && stream.connection === 'ended' && stream.steps.length === 0
  const ticker = run.company.toUpperCase()
  const queriesDone = stream.steps.filter(s => s.status === 'done' || s.status === 'error').length
  const sourcesRead = stream.steps.reduce((n, s) => n + s.sources.length, 0)
  const liveCost = stream.steps.reduce((n, s) => n + (s.cost ?? 0), 0)

  return (
    <div className="grid grid-cols-1 lg:grid-cols-[1fr_340px] gap-5 items-start">
      <div className="space-y-5 min-w-0">
        <ThesisForm
          key={run.id}
          compact
          initial={{
            company: run.company,
            thesis: run.thesis,
            mode: run.mode,
            lookback_days: run.lookback_days,
            results_per_dimension: run.results_per_dimension,
          }}
        />

        <div className="panel p-5">
          <div className="flex items-baseline gap-3">
            <h1 className="text-xl font-semibold text-stone-900">{ticker}</h1>
            {stream.ecosystem?.company_name && stream.ecosystem.company_name.toUpperCase() !== ticker && (
              <span className="text-sm text-stone-500">{stream.ecosystem.company_name}</span>
            )}
          </div>
          <div className="eyebrow mt-3 mb-1">Investment thesis</div>
          <p className="text-sm text-stone-700 leading-relaxed max-w-3xl">{run.thesis}</p>
          <div className="mt-4 flex items-baseline gap-6">
            <Count value={signals.length} label="Relevant" />
            <Count value={signals.filter(s => s.impact === 'high').length} label="High" className="text-red-600" />
            <Count value={signals.filter(s => s.impact === 'medium').length} label="Medium" className="text-amber-600" />
            <Count value={signals.filter(s => s.impact === 'low').length} label="Low" className="text-stone-500" />
            <span className="ml-auto font-mono text-[10.5px] uppercase tracking-[0.08em] text-stone-500">
              <span className="text-emerald-700">{signals.filter(s => s.direction === 'positive').length} supporting</span>
              {' · '}
              <span className="text-red-700">{signals.filter(s => s.direction === 'negative').length} challenging</span>
            </span>
          </div>
        </div>

        <ResearchTrace steps={stream.steps} running={running} />

        {failedWithoutTrace && (
          <p className="text-sm text-red-700 bg-red-50 border border-red-200 rounded-sm px-4 py-3">
            This run failed: {run.error_message || 'unknown error'}. Run it again from the form above.
          </p>
        )}
        {stream.error && (
          <p className="text-sm text-red-700 bg-red-50 border border-red-200 rounded-sm px-4 py-3">{stream.error}</p>
        )}
        {stream.connection === 'lost' && (
          <p className="text-sm text-amber-800 bg-amber-50 border border-amber-200 rounded-sm px-4 py-3">
            Lost the live connection to the backend. Refresh the page to replay this run.
          </p>
        )}

        <div className="panel px-5 py-3 flex flex-wrap items-center gap-x-6 gap-y-2">
          <FilterGroup label="Impact">
            {IMPACT_FILTERS.map(v => (
              <button key={v} className={impact === v ? 'toggle-active' : 'toggle'} onClick={() => setImpact(v)}>{v}</button>
            ))}
          </FilterGroup>
          <FilterGroup label="Direction">
            {DIRECTION_FILTERS.map(f => (
              <button key={f.value} className={direction === f.value ? 'toggle-active' : 'toggle'} onClick={() => setDirection(f.value)}>
                {f.label}
              </button>
            ))}
          </FilterGroup>
          <FilterGroup label="Dimension">
            <button className={dimension === 'all' ? 'toggle-active' : 'toggle'} onClick={() => setDimension('all')}>All</button>
            {dimensions.map(d => (
              <button key={d.key} className={dimension === d.key ? 'toggle-active' : 'toggle'} onClick={() => setDimension(d.key)}>
                {d.label}
              </button>
            ))}
          </FilterGroup>
          <FilterGroup label="Published">
            {PUBLISHED_FILTERS.map(f => (
              <button key={f.label} className={published === f.value ? 'toggle-active' : 'toggle'} onClick={() => setPublished(f.value)}>
                {f.label}
              </button>
            ))}
          </FilterGroup>
          <span className="ml-auto font-mono text-[10.5px] uppercase tracking-[0.1em] text-stone-400">
            {filtered.length} / {signals.length} signals
          </span>
        </div>

        <div className="space-y-4">
          {filtered.map((s, i) => <SignalCard key={s.id} signal={s} index={i} />)}
          {filtered.length === 0 && (
            <div className="panel px-5 py-10 text-center text-sm text-stone-500">
              {running
                ? 'Signals appear here as each Exa search finishes…'
                : signals.length === 0
                  ? 'Exa found no material signals for this thesis in the lookback window. Try a longer lookback or a deeper search mode.'
                  : 'No signals match these filters.'}
            </div>
          )}
        </div>
      </div>

      <aside className="space-y-5">
        <StatusPanel
          signals={signals}
          stats={stream.stats}
          running={running}
          mode={run.mode}
          queriesDone={queriesDone}
          sourcesRead={sourcesRead}
          liveCost={liveCost}
          elapsedMs={stream.lastEventMs}
        />
        <EcosystemPanel ecosystem={stream.ecosystem ?? run.ecosystem ?? null} ticker={ticker} />
        <PeoplePanel runId={run.id} people={run.people} />
        <AgentPanel runId={run.id} initial={run.agent} />
      </aside>
    </div>
  )
}

function Count({ value, label, className = 'text-stone-900' }: { value: number; label: string; className?: string }) {
  return (
    <span className="flex items-baseline gap-1.5">
      <span className={`text-xl font-semibold tabular-nums ${className}`}>{value}</span>
      <span className="eyebrow">{label}</span>
    </span>
  )
}

function FilterGroup({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="flex flex-wrap items-center gap-1 max-w-full">
      <span className="eyebrow mr-1">{label}</span>
      {children}
    </div>
  )
}
