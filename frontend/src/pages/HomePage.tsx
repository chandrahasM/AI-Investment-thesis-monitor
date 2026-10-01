import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { researchApi } from '../api/research'
import { ThesisForm } from '../components/ThesisForm'
import { RunList } from '../components/RunList'

const EXAMPLES = [
  {
    company: 'PLTR',
    thesis: 'High switching costs across defense, intelligence, and large corporations create entrenched, non-cancelable performance obligations for Palantir.',
  },
  {
    company: 'NVDA',
    thesis: 'CUDA and the NVIDIA software ecosystem keep hyperscalers locked in, so custom ASICs and AMD will not dent data-center share or gross margins.',
  },
  {
    company: 'TSLA',
    thesis: 'Tesla robotaxi and FSD scale faster than regulators and competitors expect, turning Tesla into an autonomy platform rather than an automaker.',
  },
]

export function HomePage() {
  const { data: config } = useQuery({ queryKey: ['research-config'], queryFn: researchApi.config })
  const [preset, setPreset] = useState<{ company: string; thesis: string } | null>(null)

  return (
    <div className="space-y-8">
      <section>
        <h1 className="text-2xl font-semibold tracking-tight text-stone-900">Turn an investment thesis into live signals</h1>
        <p className="mt-1.5 text-sm text-stone-600 max-w-3xl leading-relaxed">
          Enter a company and your thesis, then choose how hard Exa should search. Every signal below is produced live by
          Exa from today's web: nothing is pre-loaded or hard-coded.
        </p>
        <div className="mt-3 flex flex-wrap items-center gap-2">
          <span className="eyebrow">Try</span>
          {EXAMPLES.map(e => (
            <button key={e.company} className="chip hover:border-amber-600 hover:text-amber-800" onClick={() => setPreset(e)}>
              {e.company}
            </button>
          ))}
        </div>
      </section>

      <ThesisForm key={preset?.company ?? 'blank'} initial={preset ?? undefined} />

      {config && !config.exa_available && (
        <p className="text-sm text-red-700 bg-red-50 border border-red-200 rounded-sm px-4 py-3">
          EXA_API_KEY is not set in <code className="font-mono">backend/.env</code>. Research runs are disabled until it is.
        </p>
      )}

      <section className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <HowStep n="01" title="Map the ecosystem">
          One Exa search with a structured <code className="font-mono">outputSchema</code> resolves the company and pulls
          its competitors, customers, suppliers and partners.
        </HowStep>
        <HowStep n="02" title={`Search ${config?.dimensions.length ?? 6} thesis dimensions`}>
          Parallel Exa searches in your chosen mode, one per dimension (
          {config?.dimensions.map(d => d.label).join(', ') ?? 'regulation, customers, competition…'}), filtered to your lookback window.
        </HowStep>
        <HowStep n="03" title="Synthesize grounded signals">
          Exa turns the sources into signals with impact, thesis impact and direction, each with citations and a
          field-level confidence score. You watch every query and source live.
        </HowStep>
      </section>

      <section>
        <div className="flex items-baseline justify-between mb-3">
          <span className="eyebrow">Recent research</span>
          <Link to="/history" className="link-accent">All history →</Link>
        </div>
        <RunList limit={6} />
      </section>
    </div>
  )
}

function HowStep({ n, title, children }: { n: string; title: string; children: React.ReactNode }) {
  return (
    <div className="panel p-5">
      <div className="font-mono text-[11px] text-amber-700">{n}</div>
      <div className="mt-1 text-sm font-semibold text-stone-900">{title}</div>
      <p className="mt-1.5 text-xs text-stone-600 leading-relaxed">{children}</p>
    </div>
  )
}
