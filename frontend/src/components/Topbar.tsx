import { useMutation } from '@tanstack/react-query'
import { LogOut, Menu } from 'lucide-react'
import { useAuth } from '@/hooks/useAuth'

interface TopbarProps {
  onMenuClick: () => void
}

function initials(name: string | undefined): string {
  if (!name) return '?'
  const parts = name.trim().split(/\s+/)
  return ((parts[0]?.[0] ?? '') + (parts.length > 1 ? (parts[parts.length - 1]?.[0] ?? '') : '')).toUpperCase() || '?'
}

export function Topbar({ onMenuClick }: TopbarProps) {
  const { user, logout } = useAuth()
  const logoutMutation = useMutation({ mutationFn: logout })

  return (
    <header className="sticky top-0 z-20 flex h-16 items-center justify-between border-b border-glass/5 bg-[#060b09]/70 px-4 backdrop-blur-xl sm:px-6">
      <button
        onClick={onMenuClick}
        className="rounded-lg p-2 text-slate-600 hover:bg-slate-100 lg:hidden"
        aria-label="Open menu"
      >
        <Menu size={20} />
      </button>

      <div className="ml-auto flex items-center gap-3">
        <div className="hidden text-right sm:block">
          <p className="text-sm font-semibold text-slate-900">{user?.full_name}</p>
          <p className="text-xs text-slate-500">{user?.email}</p>
        </div>
        <span
          aria-hidden="true"
          className="flex h-10 w-10 items-center justify-center rounded-full bg-gradient-to-br from-emerald-500 to-amber-500 text-sm font-bold text-[#06110d] shadow-[0_0_0_3px_rgba(16,185,129,0.15)]"
        >
          {initials(user?.full_name)}
        </span>
        <button
          onClick={() => logoutMutation.mutate()}
          disabled={logoutMutation.isPending}
          className="flex items-center gap-2 rounded-xl border border-glass/10 px-3 py-2 text-sm font-medium text-slate-600 transition hover:border-glass/20 hover:bg-glass/5 hover:text-slate-900 disabled:opacity-60"
        >
          <LogOut size={16} />
          <span className="hidden sm:inline">{logoutMutation.isPending ? 'Logging out...' : 'Log out'}</span>
        </button>
      </div>
    </header>
  )
}
