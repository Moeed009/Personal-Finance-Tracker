import { useMemo } from 'react'
import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip } from 'recharts'
import { Card } from '@/components/Card'
import { useCategorySpend } from '@/hooks/useInsights'
import { formatMoney } from '@/lib/format'
import { monthLabel } from '@/lib/months'
import type { CategorySpend } from '@/types/api'

const COLORS = ['#6366f1', '#10b981', '#f59e0b', '#f43f5e', '#06b6d4', '#8b5cf6']
const MAX_SLICES = 6

interface Slice {
  name: string
  value: number
  percentage: number
}

function buildSlices(items: CategorySpend[]): Slice[] {
  const slices = items
    .map((item) => ({ name: item.category_name, value: Number(item.total), percentage: Number(item.percentage) }))
    .filter((slice) => slice.value > 0)

  if (slices.length <= MAX_SLICES) return slices

  const head = slices.slice(0, MAX_SLICES - 1)
  const rest = slices.slice(MAX_SLICES - 1)
  return [
    ...head,
    {
      name: 'Other',
      value: rest.reduce((sum, slice) => sum + slice.value, 0),
      percentage: rest.reduce((sum, slice) => sum + slice.percentage, 0),
    },
  ]
}

interface SpendingByCategoryCardProps {
  month: string
  currency: string
}

export function SpendingByCategoryCard({ month, currency }: SpendingByCategoryCardProps) {
  const query = useCategorySpend(month)
  const slices = useMemo(() => buildSlices(query.data ?? []), [query.data])

  return (
    <Card
      title="Spending by category"
      subtitle={monthLabel(month)}
      isLoading={query.isLoading}
      error={query.error}
      onRetry={() => query.refetch()}
    >
      {slices.length === 0 ? (
        <p className="py-10 text-center text-sm text-slate-500">No expenses recorded for this month.</p>
      ) : (
        <div className="flex flex-col items-center gap-6 sm:flex-row">
          <div className="h-44 w-44 shrink-0">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie data={slices} dataKey="value" nameKey="name" innerRadius={48} outerRadius={80} paddingAngle={2}>
                  {slices.map((slice, index) => (
                    <Cell key={slice.name} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip formatter={(value) => formatMoney(Number(value), currency)} />
              </PieChart>
            </ResponsiveContainer>
          </div>

          <ul className="w-full space-y-2">
            {slices.map((slice, index) => (
              <li key={slice.name} className="flex items-center justify-between gap-3 text-sm">
                <span className="flex min-w-0 items-center gap-2">
                  <span
                    className="h-2.5 w-2.5 shrink-0 rounded-full"
                    style={{ backgroundColor: COLORS[index % COLORS.length] }}
                  />
                  <span className="truncate text-slate-700">{slice.name}</span>
                </span>
                <span className="shrink-0 text-slate-900">
                  {formatMoney(slice.value, currency)}
                  <span className="ml-2 text-xs text-slate-500">{slice.percentage.toFixed(0)}%</span>
                </span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </Card>
  )
}