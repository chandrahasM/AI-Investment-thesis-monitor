import { RunList } from '../components/RunList'

export function HistoryPage() {
  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-xl font-semibold text-stone-900">Research history</h1>
        <p className="text-sm text-stone-500 mt-1">Every run is stored with its full Exa trace and can be replayed.</p>
      </div>
      <RunList allowDelete />
    </div>
  )
}
