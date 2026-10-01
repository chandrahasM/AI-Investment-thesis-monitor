export type Impact = 'high' | 'medium' | 'low'
export type Direction = 'positive' | 'negative' | 'neutral'
export type Confidence = 'high' | 'medium' | 'low'
export type RunStatus = 'pending' | 'running' | 'completed' | 'failed'

export interface SearchMode {
  value: string
  label: string
  description: string
  latency: string
}

export interface Dimension {
  key: string
  label: string
  focus?: string
}

export interface ResearchConfig {
  exa_available: boolean
  modes: SearchMode[]
  dimensions: Dimension[]
}

export interface SourceRef {
  title?: string | null
  url: string
  domain: string
  published_date?: string | null
}

export interface Citation {
  url: string
  title?: string | null
  domain: string
}

export interface ResearchSignal {
  id: string
  dimension: string
  dimension_label: string
  headline: string
  summary: string
  thesis_impact: string
  direction: Direction
  impact: Impact
  event_type?: string | null
  entities: string[]
  confidence: Confidence
  source_url: string
  source_title?: string | null
  source_domain: string
  published_date?: string | null
  highlights: string[]
  citations: Citation[]
  grounded_in_results: boolean
}

export interface Ecosystem {
  company_name: string
  sector?: string | null
  competitors: string[]
  customers: string[]
  suppliers: string[]
  partners: string[]
}

export interface RunStats {
  signals: number
  high: number
  medium: number
  low: number
  positive: number
  negative: number
  queries: number
  sources_reviewed: number
  cost: number
  elapsed_ms: number
}

export interface RunSummary {
  id: string
  company: string
  company_name?: string | null
  thesis: string
  mode: string
  lookback_days: number
  results_per_dimension: number
  status: RunStatus
  stats?: RunStats | null
  created_at: string
}

export interface Person {
  name?: string | null
  url: string
  domain: string
  highlight?: string | null
  image?: string | null
}

export interface AgentOutput {
  verdict: 'supported' | 'mixed' | 'challenged'
  summary: string
  bull_points: string[]
  bear_points: string[]
  watch_items: string[]
}

export interface AgentState {
  exa_run_id: string
  status: string
  effort: string
  text?: string | null
  structured?: AgentOutput | null
  cost?: number | null
  error?: { message?: string } | string | null
}

export interface RunDetail extends RunSummary {
  error_message?: string | null
  signals: ResearchSignal[]
  ecosystem?: Ecosystem | null
  people?: Person[] | null
  agent?: AgentState | null
}

export interface RunCreate {
  company: string
  thesis: string
  mode: string
  lookback_days: number
  results_per_dimension: number
}

export type ResearchEvent = { seq: number; t_ms: number } & (
  | { type: 'run_start'; company: string; mode: string; lookback_days: number; dimensions: Dimension[] }
  | { type: 'step_start'; step: string; label: string; query: string; search_type: string; request: Record<string, unknown> }
  | { type: 'step_sources'; step: string; sources: SourceRef[]; request_id?: string; cost: number; elapsed_ms: number }
  | { type: 'step_done'; step: string; summary: string }
  | { type: 'step_error'; step: string; error: string }
  | { type: 'signal'; signal: ResearchSignal }
  | { type: 'ecosystem'; ecosystem: Ecosystem }
  | { type: 'run_error'; error: string }
  | { type: 'run_done'; status: RunStatus; stats: RunStats }
)
