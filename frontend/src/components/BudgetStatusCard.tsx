import { Link } from 'react-router-dom'
import { Card } from '@/components/Card'
import { useBudgets } from '@/hooks/useBudgets'
import { formatMoney } from '@/lib/format'
import type { BudgetStatus } from '@/types/api'

const MAX_ITEMS = 4

const barColors: Record<BudgetStatus, string> = {
  ON_TRACK: 'bg-emerald-500',
  WARNING: 'bg-amber-500',
  EXCEEDED: 'bg-rose-500',
}

interface BudgetStatusCardProps {
  month: string
  currency: string
}

export function BudgetStatusCard({ month, currency }: BudgetStatusCardProps) {
  const query = useBudgets(month)
  const items = [...(query.data ?? [])]
    .sort((a, b) => Number(b.percent_used) - Number(a.percent_used))
    .slice(0, MAX_ITEMS)

  return (
    <Card
      title="Budgets"
      subtitle="Closest to their limit"
      isLoading={query.isLoading}
      error={query.error}
      onRetry={() => query.refetch()}
      action={
        <Link to={`/budgets?month=${month}`} className="text-sm font-medium text-indigo-600 hover:underline">
          View all
        </Link>
      }
    >
      {items.length === 0 ? (
        <div className="py-8 text-center">
          <p className="text-sm text-slate-500">No budgets set for this month.</p>
          <Link
            to={`/budgets?month=${month}`}
            className="mt-2 inline-block text-sm font-medium text-indigo-600 hover:underline"
          >
            Create a budget
          </Link>
        </div>
      ) : (
        <ul className="space-y-4">
          {items.map((budget) => {
            const percent = Number(budget.percent_used)
            return (
              <li key={budget.id}>
                <div className="flex items-baseline justify-between text-sm">
                  <span className="font-medium text-slate-900">{budget.category_name}</span>
                  <span className="text-slate-500">
                    {formatMoney(budget.spent, currency)} / {formatMoney(budget.limit_amount, currency)}
                  </span>
                </div>
                <div className="mt-1.5 h-2 overflow-hidden rounded-full bg-slate-100">
                  <div
                    className={`h-full rounded-full ${barColors[budget.status]}`}
                    style={{ width: `${Math.min(100, percent)}%` }}
                  />
                </div>
              </li>
            )
          })}
        </ul>
      )}
    </Card>
  )
}