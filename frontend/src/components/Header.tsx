import { Link, NavLink } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { researchApi } from '../api/research'

export function Header() {
  const { data: config } = useQuery({ queryKey: ['research-config'], queryFn: researchApi.config })

  const navClass = ({ isActive }: { isActive: boolean }) =>
    `font-mono text-[11px] uppercase tracking-[0.14em] ${isActive ? 'text-stone-900' : 'text-stone-500 hover:text-stone-900'}`

  return (
    <header className="bg-white border-b border-stone-200 sticky top-0 z-30">
      <div className="max-w-[1400px] mx-auto px-6 h-14 flex items-center gap-4">
        <Link to="/" className="flex items-baseline gap-3">
          <span className="text-[15px] font-semibold tracking-tight text-stone-900">Signal</span>
          <span className="eyebrow hidden sm:inline">Buy-side equity intelligence</span>
        </Link>
        <nav className="ml-auto flex items-center gap-6">
          <NavLink to="/" end className={navClass}>New research</NavLink>
          <NavLink to="/history" className={navClass}>History</NavLink>
          {config && (
            <span className="flex items-center gap-1.5 eyebrow">
              <span className={`h-1.5 w-1.5 rounded-full ${config.exa_available ? 'bg-emerald-500' : 'bg-red-500'}`} />
              {config.exa_available ? 'Exa live' : 'Exa key missing'}
            </span>
          )}
        </nav>
      </div>
    </header>
  )
}
