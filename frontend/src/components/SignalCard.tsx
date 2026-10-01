import { useState } from 'react'
import { ExternalLink } from 'lucide-react'
import type { Direction, Impact, ResearchSignal } from '../types/research'
import { faviconUrl, relativeAge, shortDate } from '../lib/format'

const IMPACT_STYLE: Record<Impact, string> = {
  high: 'border-red-300 bg-red-50 text-red-700',
  medium: 'border-amber-400 bg-amber-50 text-amber-800',
  low: 'border-stone-300 bg-stone-50 text-stone-600',
}

const DIRECTION_STYLE: Record<Direction, { label: string; className: string }> = {
  positive: { label: 'Potentially positive', className: 'border-emerald-300 bg-emerald-50 text-emerald-700' },
  negative: { label: 'Potentially negative', className: 'border-red-300 bg-red-50 text-red-700' },
  neutral: { label: 'Neutral', className: 'border-stone-300 bg-stone-50 text-stone-600' },
}

const CONFIDENCE_STYLE = {
  high: 'text-emerald-700',
  medium: 'text-amber-700',
  low: 'text-stone-500',
}

export function SignalCard({ signal, index }: { signal: ResearchSignal; index: number }) {
  const [open, setOpen] = useState(false)
  const direction = DIRECTION_STYLE[signal.direction]

  return (
    <article
      className="panel animate-fadeIn"
      style={{ animationDelay: `${Math.min(index, 10) * 40}ms` }}
    >
      <div className="p-5">
        <div className="flex items-center gap-2">
          <span className={`mono-tag ${IMPACT_STYLE[signal.impact]}`}>{signal.impact} impact</span>
          <span className="mono-tag border-stone-200 text-stone-500">{signal.dimension_label}</span>
          <span className="ml-auto font-mono text-[10.5px] uppercase tracking-[0.1em] text-stone-400">
            {relativeAge(signal.published_date)}
          </span>
        </div>

        <h3 className="mt-3 text-[15px] font-semibold leading-snug text-stone-900">
          <a href={signal.source_url} target="_blank" rel="noreferrer" className="hover:text-amber-800">
            {signal.headline}
          </a>
        </h3>
        {signal.event_type && <div className="eyebrow mt-1">{signal.event_type}</div>}

        <p className="mt-3 text-sm leading-relaxed text-stone-700">{signal.summary}</p>

        <div className="mt-3 border-l-2 border-amber-500 bg-amber-50/40 pl-3 py-2 pr-2">
          <div className="eyebrow mb-1">Thesis impact</div>
          <p className="text-sm leading-relaxed text-stone-700">{signal.thesis_impact}</p>
        </div>

        {signal.entities.length > 0 && (
          <div className="mt-3 flex flex-wrap gap-1.5">
            {signal.entities.map(e => <span key={e} className="chip">{e}</span>)}
          </div>
        )}
      </div>

      <div className="border-t border-stone-100 px-5 py-3 flex items-center gap-x-5 gap-y-2 flex-wrap">
        <span className={`mono-tag ${direction.className}`}>{direction.label}</span>
        <span className="flex items-center gap-1.5 font-mono text-[10.5px] uppercase tracking-[0.08em] text-stone-500">
          Source
          <img src={faviconUrl(signal.source_domain)} alt="" className="h-3 w-3" loading="lazy" />
          <span className="normal-case tracking-normal text-stone-700">{signal.source_domain}</span>
        </span>
        <span className="font-mono text-[10.5px] uppercase tracking-[0.08em] text-stone-500">
          Published <span className="normal-case tracking-normal text-stone-700">{shortDate(signal.published_date)}</span>
        </span>
        <span className="font-mono text-[10.5px] uppercase tracking-[0.08em] text-stone-500">
          Confidence <span className={`normal-case tracking-normal ${CONFIDENCE_STYLE[signal.confidence]}`}>{signal.confidence}</span>
        </span>
        <button className="link-accent ml-auto" onClick={() => setOpen(!open)}>
          {open ? 'Hide evidence ↑' : 'View evidence →'}
        </button>
      </div>

      {open && (
        <div className="border-t border-stone-100 bg-stone-50/60 px-5 py-4 space-y-4">
          <div>
            <div className="eyebrow mb-2">Source excerpt returned by Exa</div>
            {signal.highlights.length > 0 ? (
              <div className="space-y-2">
                {signal.highlights.map((h, i) => (
                  <blockquote key={i} className="text-sm text-stone-700 leading-relaxed border-l-2 border-stone-300 pl-3 italic">
                    “{h.trim()}”
                  </blockquote>
                ))}
              </div>
            ) : (
              <p className="text-xs text-stone-500">No excerpt was returned for this source.</p>
            )}
            <a
              href={signal.source_url}
              target="_blank"
              rel="noreferrer"
              className="mt-2 inline-flex items-center gap-1 text-xs text-amber-800 hover:underline"
            >
              {signal.source_title || signal.source_url}
              <ExternalLink className="h-3 w-3" />
            </a>
          </div>

          {signal.citations.length > 0 && (
            <div>
              <div className="eyebrow mb-2">Grounding citations ({signal.citations.length})</div>
              <ul className="space-y-1">
                {signal.citations.map(c => (
                  <li key={c.url} className="flex items-center gap-2 text-xs">
                    <img src={faviconUrl(c.domain)} alt="" className="h-3 w-3" loading="lazy" />
                    <a href={c.url} target="_blank" rel="noreferrer" className="text-stone-700 hover:text-amber-800 hover:underline truncate">
                      {c.title || c.url}
                    </a>
                  </li>
                ))}
              </ul>
            </div>
          )}

          <p className="text-[11px] text-stone-500">
            Synthesized by Exa <code className="font-mono">outputSchema</code> from the search results; confidence is
            Exa's field-level grounding score.
            {!signal.grounded_in_results && ' The cited URL was not in the returned result set.'}
          </p>
        </div>
      )}
    </article>
  )
}
