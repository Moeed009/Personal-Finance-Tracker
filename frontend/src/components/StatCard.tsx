import type { LucideIcon } from 'lucide-react'

type Tone = 'default' | 'positive' | 'negative'

interface StatCardProps {
  label: string
  value?: string
  hint?: string
  icon: LucideIcon
  tone?: Tone
  isLoading?: boolean
}

const valueTones: Record<Tone, string> = {
  default: 'text-slate-900',
  positive: 'text-emerald-700',
  negative: 'text-rose-700',
}

const iconTones: Record<Tone, string> = {
  default: 'bg-amber-500/15 text-amber-700',
  positive: 'bg-emerald-500/15 text-emerald-600',
  negative: 'bg-rose-500/15 text-rose-600',
}

export function StatCard({ label, value, hint, icon: Icon, tone = 'default', isLoading = false }: StatCardProps) {
  return (
    <div className="card-lift animate-rise rounded-3xl bg-white p-5 shadow-sm ring-1 ring-slate-200 hover:ring-emerald-500/30">
      <div className="flex items-center gap-3">
        <span className={`flex h-10 w-10 items-center justify-center rounded-xl ${iconTones[tone]}`}>
          <Icon size={18} />
        </span>
        <p className="text-sm font-semibold text-slate-600">{label}</p>
      </div>

      {isLoading ? (
        <div className="mt-4 h-8 w-32 animate-pulse rounded-lg bg-slate-200" />
      ) : (
        <p className={`mt-4 font-display text-2xl font-semibold tracking-tight ${valueTones[tone]}`}>{value ?? '—'}</p>
      )}

      {hint && !isLoading && <p className="mt-1 text-xs font-medium text-slate-500">{hint}</p>}
    </div>
  )
}
