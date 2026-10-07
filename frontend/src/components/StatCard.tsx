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

const tones: Record<Tone, string> = {
  default: 'text-slate-900',
  positive: 'text-emerald-600',
  negative: 'text-rose-600',
}

export function StatCard({ label, value, hint, icon: Icon, tone = 'default', isLoading = false }: StatCardProps) {
  return (
    <div className="rounded-xl bg-white p-5 shadow-sm ring-1 ring-slate-200">
      <div className="flex items-center justify-between">
        <p className="text-sm text-slate-500">{label}</p>
        <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-indigo-50 text-indigo-600">
          <Icon size={16} />
        </span>
      </div>

      {isLoading ? (
        <div className="mt-3 h-8 w-32 animate-pulse rounded bg-slate-200" />
      ) : (
        <p className={`mt-2 text-2xl font-semibold ${tones[tone]}`}>{value ?? '—'}</p>
      )}

      {hint && !isLoading && <p className="mt-1 text-xs text-slate-500">{hint}</p>}
    </div>
  )
}