import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Loader2 } from 'lucide-react'
import { researchApi } from '../api/research'
import type { AgentState, Ecosystem, Person, ResearchSignal, RunStats } from '../types/research'
import { faviconUrl, formatCost, formatMs } from '../lib/format'

// ── Research status ──────────────────────────────────────────────────────────

interface StatusPanelProps {
  signals: ResearchSignal[]
  stats: RunStats | null
  running: boolean
  mode: string
  queriesDone: number
  sourcesRead: number
  liveCost: number
  elapsedMs: number
}

export function StatusPanel({ signals, stats, running, mode, queriesDone, sourcesRead, liveCost, elapsedMs }: StatusPanelProps) {
  const count = (impact: string) => signals.filter(s => s.impact === impact).length
  return (
    <div className="panel p-5">
      <div className="flex items-center justify-between mb-4">
        <span className="eyebrow">Research status</span>
        <span className={`font-mono text-[10.5px] uppercase tracking-[0.1em] ${running ? 'text-amber-700' : 'text-emerald-700'}`}>
          {running ? 'Running' : 'Complete'}
        </span>
      </div>
      <div className="grid grid-cols-2 gap-y-3">
        <Stat value={signals.length} label="Signals" />
        <Stat value={count('high')} label="High impact" className="text-red-600" />
        <Stat value={count('medium')} label="Medium" className="text-amber-600" />
        <Stat value={count('low')} label="Low" className="text-stone-500" />
      </div>
      <div className="mt-4 pt-3 border-t border-stone-100 grid grid-cols-2 gap-y-1.5 font-mono text-[10.5px] uppercase tracking-[0.08em] text-stone-500">
        <span>Mode <b className="text-stone-800 font-medium normal-case">{mode}</b></span>
        <span>Exa queries <b className="text-stone-800 font-medium">{stats?.queries ?? queriesDone}</b></span>
        <span>Sources <b className="text-stone-800 font-medium">{stats?.sources_reviewed ?? sourcesRead}</b></span>
        <span>Cost <b className="text-stone-800 font-medium">{formatCost(stats?.cost ?? liveCost)}</b></span>
        <span>Time <b className="text-stone-800 font-medium">{formatMs(stats?.elapsed_ms ?? elapsedMs)}</b></span>
      </div>
    </div>
  )
}

function Stat({ value, label, className = 'text-stone-900' }: { value: number; label: string; className?: string }) {
  return (
    <div className="flex items-baseline gap-2">
      <span className={`text-xl font-semibold tabular-nums ${className}`}>{value}</span>
      <span className="eyebrow">{label}</span>
    </div>
  )
}

// ── Ecosystem ────────────────────────────────────────────────────────────────

export function EcosystemPanel({ ecosystem, ticker }: { ecosystem: Ecosystem | null; ticker: string }) {
  const groups: { key: keyof Ecosystem; label: string }[] = [
    { key: 'competitors', label: 'Competitors' },
    { key: 'customers', label: 'Customers' },
    { key: 'suppliers', label: 'Suppliers' },
    { key: 'partners', label: 'Partners' },
  ]
  return (
    <div className="panel p-5">
      <div className="eyebrow mb-1">{ticker} ecosystem</div>
      {!ecosystem ? (
        <p className="text-xs text-stone-500 mt-2 flex items-center gap-2">
          <Loader2 className="h-3 w-3 animate-spin" /> Mapping with Exa…
        </p>
      ) : (
        <>
          {ecosystem.sector && <div className="text-sm font-semibold text-stone-900 mb-3">{ecosystem.sector}</div>}
          <div className="space-y-3">
            {groups.map(g => {
              const items = ecosystem[g.key] as string[]
              if (!items?.length) return null
              return (
                <div key={g.key}>
                  <div className="eyebrow text-[10px] mb-1.5">{g.label}</div>
                  <div className="flex flex-wrap gap-1.5">
                    {items.map(i => <span key={i} className="chip">{i}</span>)}
                  </div>
                </div>
              )
            })}
          </div>
        </>
      )}
    </div>
  )
}

// ── People ───────────────────────────────────────────────────────────────────

export function PeoplePanel({ runId, people }: { runId: string; people?: Person[] | null }) {
  const queryClient = useQueryClient()
  const find = useMutation({
    mutationFn: () => researchApi.findPeople(runId),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['research-run', runId] }),
  })
  const list = find.data ?? people

  return (
    <div className="panel p-5">
      <div className="flex items-center justify-between mb-2">
        <span className="eyebrow">Relevant people</span>
        <button className="btn-outline px-3 py-1.5" disabled={find.isPending} onClick={() => find.mutate()}>
          {find.isPending ? 'Searching…' : list ? 'Refresh' : 'Find people'}
        </button>
      </div>
      {!list && !find.isPending && (
        <p className="text-xs text-stone-500 leading-relaxed">
          Runs an Exa search with <code className="font-mono">category: "people"</code> for the executives whose moves tend
          to precede changes in this thesis.
        </p>
      )}
      {find.isError && <p className="text-xs text-red-700 mt-2">{(find.error as Error).message}</p>}
      {list && list.length === 0 && <p className="text-xs text-stone-500">No profiles returned.</p>}
      {list && list.length > 0 && (
        <ul className="divide-y divide-stone-100 mt-1">
          {list.map(p => (
            <li key={p.url} className="py-2.5">
              <a href={p.url} target="_blank" rel="noreferrer" className="flex items-center gap-2 text-sm font-medium text-stone-900 hover:text-amber-800">
                <img src={faviconUrl(p.domain)} alt="" className="h-3.5 w-3.5" loading="lazy" />
                <span className="truncate">{p.name || p.url}</span>
              </a>
              {p.highlight && <p className="text-xs text-stone-500 mt-0.5 line-clamp-2">{p.highlight}</p>}
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}

// ── Deep research (Exa Agent) ────────────────────────────────────────────────

const EFFORTS = [
  { value: 'minimal', label: 'Minimal', price: '$0.012' },
  { value: 'low', label: 'Low', price: '$0.025' },
  { value: 'medium', label: 'Medium', price: '$0.10' },
  { value: 'high', label: 'High', price: '$0.50' },
]
const TERMINAL = ['completed', 'failed', 'cancelled']

const VERDICT_STYLE = {
  supported: 'border-emerald-300 bg-emerald-50 text-emerald-700',
  mixed: 'border-amber-400 bg-amber-50 text-amber-800',
  challenged: 'border-red-300 bg-red-50 text-red-700',
}

export function AgentPanel({ runId, initial }: { runId: string; initial?: AgentState | null }) {
  const queryClient = useQueryClient()
  const [effort, setEffort] = useState('low')
  const [started, setStarted] = useState(Boolean(initial))

  const start = useMutation({
    mutationFn: () => researchApi.startAgent(runId, effort),
    onSuccess: () => {
      setStarted(true)
      queryClient.invalidateQueries({ queryKey: ['agent', runId] })
    },
  })

  const { data: agent, error: pollError } = useQuery({
    queryKey: ['agent', runId],
    queryFn: () => researchApi.pollAgent(runId),
    enabled: started,
    initialData: initial ?? undefined,
    refetchInterval: q => (q.state.data && TERMINAL.includes(q.state.data.status) ? false : 5000),
  })

  const active = agent && !TERMINAL.includes(agent.status)
  const out = agent?.structured

  return (
    <div className="panel p-5">
      <div className="flex items-center justify-between mb-2">
        <span className="eyebrow">Deep research</span>
        <span className="font-mono text-[10px] text-stone-400">Exa Agent</span>
      </div>

      {(!agent || TERMINAL.includes(agent.status)) && (
        <>
          <p className="text-xs text-stone-500 leading-relaxed mb-3">
            Exa Agent fans out many searches, reads the pages and returns a grounded bull / bear verdict on the thesis.
          </p>
          <div className="flex flex-wrap gap-1 mb-3">
            {EFFORTS.map(e => (
              <button key={e.value} className={effort === e.value ? 'toggle-active' : 'toggle'} onClick={() => setEffort(e.value)}>
                {e.label} <span className="opacity-60">{e.price}</span>
              </button>
            ))}
          </div>
          <button className="btn-outline w-full" disabled={start.isPending} onClick={() => start.mutate()}>
            {start.isPending ? 'Starting…' : agent ? 'Run again' : 'Run Exa Agent'}
          </button>
        </>
      )}

      {(start.isError || pollError) && (
        <p className="text-xs text-red-700 mt-2">{((start.error || pollError) as Error).message}</p>
      )}

      {active && (
        <div className="flex items-center gap-2 text-xs text-amber-700 mt-1">
          <Loader2 className="h-3.5 w-3.5 animate-spin" />
          Agent {agent.status} · effort {agent.effort} · polling every 5s
        </div>
      )}

      {agent?.status === 'failed' && (
        <p className="text-xs text-red-700 mt-3">
          Agent run failed{typeof agent.error === 'object' && agent.error?.message ? `: ${agent.error.message}` : ''}
        </p>
      )}

      {agent?.status === 'completed' && (
        <div className="mt-4 pt-4 border-t border-stone-100 space-y-3">
          {out ? (
            <>
              <div className="flex items-center gap-2">
                <span className={`mono-tag ${VERDICT_STYLE[out.verdict] || VERDICT_STYLE.mixed}`}>Thesis {out.verdict}</span>
                {agent.cost != null && <span className="font-mono text-[10px] text-stone-400">{formatCost(agent.cost)}</span>}
              </div>
              <p className="text-sm text-stone-700 leading-relaxed">{out.summary}</p>
              <AgentList title="Bull case" items={out.bull_points} tone="text-emerald-700" />
              <AgentList title="Bear case" items={out.bear_points} tone="text-red-700" />
              <AgentList title="Watch next" items={out.watch_items} tone="text-stone-700" />
            </>
          ) : (
            <p className="text-sm text-stone-700 whitespace-pre-wrap">{agent.text}</p>
          )}
        </div>
      )}
    </div>
  )
}

function AgentList({ title, items, tone }: { title: string; items: string[]; tone: string }) {
  if (!items?.length) return null
  return (
    <div>
      <div className={`eyebrow mb-1 ${tone}`}>{title}</div>
      <ul className="space-y-1">
        {items.map((i, n) => (
          <li key={n} className="text-xs text-stone-700 leading-relaxed pl-3 relative">
            <span className="absolute left-0 text-stone-400">–</span>
            {i}
          </li>
        ))}
      </ul>
    </div>
  )
}
