import { AlertTriangle, CheckCircle2 } from 'lucide-react'
import { Card } from '@/components/Card'
import { useUnusualSpending } from '@/hooks/useInsights'
import { formatDay, formatMoney } from '@/lib/format'
import { monthLabel } from '@/lib/months'

interface UnusualSpendingCardProps {
  month: string
  currency: string
}

export function UnusualSpendingCard({ month, currency }: UnusualSpendingCardProps) {
  const query = useUnusualSpending(month)
  const items = query.data ?? []

  return (
    <Card
      title="Unusual spending"
      subtitle={monthLabel(month)}
      isLoading={query.isLoading}
      error={query.error}
      onRetry={() => query.refetch()}
    >
      {items.length === 0 ? (
        <div className="py-8 text-center">
          <CheckCircle2 className="mx-auto text-emerald-500" size={28} />
          <p className="mt-2 text-sm font-medium text-slate-900">Nothing unusual this month</p>
          <p className="mt-1 text-xs text-slate-500">Detection needs a few months of spending history.</p>
        </div>
      ) : (
        <ul className="divide-y divide-slate-100">
          {items.map((item) => (
            <li key={item.transaction_id ?? `${item.kind}-${item.category_id}`} className="flex gap-3 py-3">
              <AlertTriangle className="mt-0.5 shrink-0 text-amber-500" size={18} />
              <div className="min-w-0 text-sm">
                <p className="font-medium text-slate-900">
                  {item.category_name}
                  <span className="ml-2 text-xs font-normal text-slate-500">
                    {item.kind === 'TRANSACTION' ? 'Large expense' : 'Monthly spike'}
                    {item.detected_at ? ` · ${formatDay(item.detected_at)}` : ''}
                  </span>
                </p>
                <p className="text-slate-600">
                  {formatMoney(item.amount, currency)} (usual limit {formatMoney(item.threshold, currency)})
                  {item.deviation_percent && Number(item.deviation_percent) > 0 && (
                    <span className="text-rose-600"> · {Number(item.deviation_percent).toFixed(0)}% above average</span>
                  )}
                </p>
              </div>
            </li>
          ))}
        </ul>
      )}
    </Card>
  )
}