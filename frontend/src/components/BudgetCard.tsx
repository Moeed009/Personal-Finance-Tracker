import { Pencil, Trash2 } from 'lucide-react'
import { formatMoney } from '@/lib/format'
import type { Budget, BudgetStatus } from '@/types/api'

interface BudgetCardProps {
  budget: Budget
  currency: string
  onEdit: () => void
  onDelete: () => void
}

const statusStyles: Record<BudgetStatus, { bar: string; badge: string; label: string }> = {
  ON_TRACK: { bar: 'bg-emerald-500', badge: 'bg-emerald-50 text-emerald-700', label: 'On track' },
  WARNING: { bar: 'bg-amber-500', badge: 'bg-amber-50 text-amber-700', label: 'Warning' },
  EXCEEDED: { bar: 'bg-rose-500', badge: 'bg-rose-50 text-rose-700', label: 'Exceeded' },
}

export function BudgetCard({ budget, currency, onEdit, onDelete }: BudgetCardProps) {
  const styles = statusStyles[budget.status]
  const percent = Number(budget.percent_used)
  const remaining = Number(budget.remaining)

  return (
    <div className="rounded-xl bg-white p-5 shadow-sm ring-1 ring-slate-200">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <p className="truncate font-medium text-slate-900">{budget.category_name}</p>
          <span className={`mt-1 inline-block rounded-full px-2.5 py-0.5 text-xs font-medium ${styles.badge}`}>
            {styles.label}
          </span>
        </div>
        <div className="flex shrink-0 gap-1">
          <button
            onClick={onEdit}
            className="rounded-md p-2 text-slate-400 hover:bg-slate-100 hover:text-slate-700"
            aria-label={`Edit ${budget.category_name} budget`}
          >
            <Pencil size={16} />
          </button>
          <button
            onClick={onDelete}
            className="rounded-md p-2 text-slate-400 hover:bg-rose-50 hover:text-rose-600"
            aria-label={`Delete ${budget.category_name} budget`}
          >
            <Trash2 size={16} />
          </button>
        </div>
      </div>

      <div className="mt-4 h-2 overflow-hidden rounded-full bg-slate-100">
        <div className={`h-full rounded-full ${styles.bar}`} style={{ width: `${Math.min(100, percent)}%` }} />
      </div>

      <div className="mt-3 flex items-baseline justify-between text-sm">
        <span className="text-slate-900">
          <span className="font-semibold">{formatMoney(budget.spent, currency)}</span>
          <span className="text-slate-500"> of {formatMoney(budget.limit_amount, currency)}</span>
        </span>
        <span className="font-medium text-slate-600">{percent.toFixed(0)}%</span>
      </div>

      <p className={`mt-1 text-xs ${remaining < 0 ? 'text-rose-600' : 'text-slate-500'}`}>
        {remaining >= 0
          ? `${formatMoney(remaining, currency)} left`
          : `${formatMoney(Math.abs(remaining), currency)} over budget`}
      </p>
    </div>
  )
}