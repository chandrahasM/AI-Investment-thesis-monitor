import { useEffect, useReducer } from 'react'
import { researchApi } from '../api/research'
import type {
  Dimension, Ecosystem, ResearchEvent, ResearchSignal, RunStats, RunStatus, SourceRef,
} from '../types/research'

export interface TraceStep {
  key: string
  label: string
  status: 'queued' | 'running' | 'done' | 'error'
  query?: string
  searchType?: string
  request?: Record<string, unknown>
  sources: SourceRef[]
  requestId?: string
  cost?: number
  elapsedMs?: number
  summary?: string
  error?: string
  startedAtMs?: number
}

export interface StreamState {
  connection: 'connecting' | 'live' | 'ended' | 'lost'
  status: RunStatus | null
  steps: TraceStep[]
  signals: ResearchSignal[]
  ecosystem: Ecosystem | null
  stats: RunStats | null
  error: string | null
  lastEventMs: number
}

const initialState: StreamState = {
  connection: 'connecting',
  status: null,
  steps: [],
  signals: [],
  ecosystem: null,
  stats: null,
  error: null,
  lastEventMs: 0,
}

type Action =
  | { type: 'reset' }
  | { type: 'event'; event: ResearchEvent }
  | { type: 'ended' }
  | { type: 'lost' }

function updateStep(steps: TraceStep[], key: string, patch: Partial<TraceStep>, label?: string): TraceStep[] {
  const exists = steps.some(s => s.key === key)
  if (!exists) {
    return [...steps, { key, label: label || key, status: 'queued', sources: [], ...patch }]
  }
  return steps.map(s => (s.key === key ? { ...s, ...patch } : s))
}

function reducer(state: StreamState, action: Action): StreamState {
  switch (action.type) {
    case 'reset':
      return initialState
    case 'ended':
      return { ...state, connection: 'ended' }
    case 'lost':
      return { ...state, connection: state.connection === 'ended' ? 'ended' : 'lost' }
    case 'event':
      break
  }

  const ev = action.event
  const next: StreamState = { ...state, connection: 'live', lastEventMs: ev.t_ms }

  switch (ev.type) {
    case 'run_start': {
      const queued: TraceStep[] = [
        { key: 'ecosystem', label: 'Map company ecosystem', status: 'queued', sources: [] },
        ...ev.dimensions.map((d: Dimension) => ({ key: d.key, label: d.label, status: 'queued' as const, sources: [] })),
      ]
      return { ...next, status: 'running', steps: queued }
    }
    case 'step_start':
      return {
        ...next,
        steps: updateStep(state.steps, ev.step, {
          label: ev.label, status: 'running', query: ev.query,
          searchType: ev.search_type, request: ev.request, startedAtMs: ev.t_ms,
        }, ev.label),
      }
    case 'step_sources':
      return {
        ...next,
        steps: updateStep(state.steps, ev.step, {
          sources: ev.sources, requestId: ev.request_id, cost: ev.cost, elapsedMs: ev.elapsed_ms,
        }),
      }
    case 'step_done':
      return { ...next, steps: updateStep(state.steps, ev.step, { status: 'done', summary: ev.summary }) }
    case 'step_error':
      return { ...next, steps: updateStep(state.steps, ev.step, { status: 'error', error: ev.error }) }
    case 'signal':
      if (state.signals.some(s => s.id === ev.signal.id || s.source_url === ev.signal.source_url)) return next
      return { ...next, signals: [...state.signals, ev.signal] }
    case 'ecosystem':
      return { ...next, ecosystem: ev.ecosystem }
    case 'run_error':
      return { ...next, error: ev.error }
    case 'run_done':
      return { ...next, status: ev.status, stats: ev.stats }
    default:
      return next
  }
}

/** Replays a run's full event log from the server, then tails live events until the run ends. */
export function useResearchStream(runId: string | undefined) {
  const [state, dispatch] = useReducer(reducer, initialState)

  useEffect(() => {
    if (!runId) return
    dispatch({ type: 'reset' })
    const source = new EventSource(researchApi.streamUrl(runId))
    source.onmessage = message => {
      const event = JSON.parse(message.data)
      if (event.type === 'stream_end') {
        source.close()
        dispatch({ type: 'ended' })
        return
      }
      dispatch({ type: 'event', event })
    }
    source.onerror = () => {
      source.close()
      dispatch({ type: 'lost' })
    }
    return () => source.close()
  }, [runId])

  return state
}
