import { NavLink } from 'react-router-dom'
import { Upload, X } from 'lucide-react'
import { Logo } from '@/components/Logo'
import { navItems } from '@/lib/navigation'

interface SidebarProps {
  open: boolean
  onClose: () => void
}

export function Sidebar({ open, onClose }: SidebarProps) {
  return (
    <>
      {open && (
        <div className="fixed inset-0 z-30 bg-slate-900/40 lg:hidden" onClick={onClose} aria-hidden="true" />
      )}

      <aside
        className={`fixed inset-y-0 left-0 z-40 flex w-64 flex-col border-r border-glass/5 bg-[#0a120f]/95 backdrop-blur-xl transition-transform duration-300 lg:translate-x-0 ${
          open ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        <div className="flex h-20 items-center justify-between px-6">
          <Logo size={38} subtitle="Personal finance" />
          <button
            onClick={onClose}
            className="rounded-lg p-2 text-slate-500 hover:bg-slate-100 lg:hidden"
            aria-label="Close menu"
          >
            <X size={20} />
          </button>
        </div>

        <nav aria-label="Main" className="flex-1 space-y-1 overflow-y-auto px-4 py-2">
          {navItems.map(({ to, label, icon: Icon, end }) => (
            <NavLink
              key={to}
              to={to}
              end={end}
              onClick={onClose}
              className={({ isActive }) =>
                `group flex items-center gap-3 rounded-xl px-3.5 py-2.5 text-sm font-medium transition-all duration-200 ${
                  isActive
                    ? 'bg-gradient-to-r from-emerald-500/25 to-emerald-500/5 text-slate-900 shadow-[inset_0_0_0_1px_rgba(52,211,153,0.25)]'
                    : 'text-slate-600 hover:bg-glass/5 hover:text-slate-900'
                }`
              }
            >
              {({ isActive }) => (
                <>
                  <Icon
                    size={18}
                    className={isActive ? 'text-emerald-600' : 'text-slate-500 transition-colors group-hover:text-slate-700'}
                  />
                  {label}
                </>
              )}
            </NavLink>
          ))}
        </nav>

        <div className="m-4 rounded-2xl border border-amber-500/25 bg-gradient-to-br from-amber-500/15 to-emerald-500/10 p-4">
          <p className="font-display text-sm font-semibold text-slate-900">Import a statement</p>
          <p className="mt-1 text-xs leading-relaxed text-slate-600">
            Upload a CSV or PDF from your bank or wallet.
          </p>
          <NavLink
            to="/imports"
            onClick={onClose}
            className="mt-3 inline-flex items-center gap-1.5 text-xs font-bold text-amber-700 hover:text-amber-800"
          >
            <Upload size={14} />
            Upload file
          </NavLink>
        </div>
      </aside>
    </>
  )
}
