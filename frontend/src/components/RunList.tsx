import { Link } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Trash2 } from 'lucide-react'
import { researchApi } from '../api/research'
import { relativeAge } from '../lib/format'

const STATUS_STYLE: Record<string, string> = {
  completed: 'text-emerald-700',
  running: 'text-amber-700',
  pending: 'text-amber-700',
  failed: 'text-red-700',
}

export function RunList({ limit, allowDelete }: { limit?: number; allowDelete?: boolean }) {
  const queryClient = useQueryClient()
  const { data: runs = [], isLoading } = useQuery({ queryKey: ['research-runs'], queryFn: researchApi.list })
  const remove = useMutation({
    mutationFn: (id: string) => researchApi.remove(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['research-runs'] }),
  })

  const shown = limit ? runs.slice(0, limit) : runs

  if (isLoading) return <p className="text-xs text-stone-500">Loading…</p>
  if (shown.length === 0) {
    return <p className="text-sm text-stone-500">No research yet. Enter a company and thesis above to run your first one.</p>
  }

  return (
    <div className="panel divide-y divide-stone-100">
      {shown.map(run => (
        <div key={run.id} className="flex items-center gap-4 px-5 py-3.5 hover:bg-stone-50 group">
          <Link to={`/research/${run.id}`} className="flex-1 min-w-0 flex items-center gap-4">
            <span className="w-16 flex-shrink-0 text-sm font-semibold text-stone-900">{run.company}</span>
            <span className="flex-1 min-w-0 text-sm text-stone-600 truncate">{run.thesis}</span>
            <span className="hidden md:inline mono-tag border-stone-200 text-stone-500">{run.mode}</span>
            {run.stats && (
              <span className="hidden md:inline font-mono text-[10.5px] text-stone-500 w-28 text-right">
                {run.stats.signals} signals · <span className="text-red-600">{run.stats.high} high</span>
              </span>
            )}
            <span className={`font-mono text-[10.5px] uppercase tracking-[0.08em] w-20 text-right ${STATUS_STYLE[run.status]}`}>
              {run.status}
            </span>
            <span className="font-mono text-[10.5px] text-stone-400 w-16 text-right">{relativeAge(run.created_at)}</span>
          </Link>
          {allowDelete && (
            <button
              className="text-stone-300 hover:text-red-600 disabled:opacity-30"
              disabled={run.status === 'running' || run.status === 'pending' || remove.isPending}
              onClick={() => remove.mutate(run.id)}
              title="Delete run"
            >
              <Trash2 className="h-3.5 w-3.5" />
            </button>
          )}
        </div>
      ))}
    </div>
  )
}
