import { useMemo } from 'react'
import { Bar, BarChart, CartesianGrid, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { Card } from '@/components/Card'
import { TREND_MONTHS, useTrends } from '@/hooks/useInsights'
import { formatCompact, formatMoney } from '@/lib/format'
import { shortMonthLabel } from '@/lib/months'

export function TrendsCard({ currency }: { currency: string }) {
  const query = useTrends()

  const data = useMemo(
    () =>
      (query.data ?? []).map((point) => ({
        month: shortMonthLabel(point.month),
        Income: Number(point.income),
        Expenses: Number(point.expense),
      })),
    [query.data],
  )
  const hasData = data.some((point) => point.Income > 0 || point.Expenses > 0)

  return (
    <Card
      title="Income vs expenses"
      subtitle={`Last ${TREND_MONTHS} months`}
      isLoading={query.isLoading}
      error={query.error}
      onRetry={() => query.refetch()}
    >
      {!hasData ? (
        <p className="py-10 text-center text-sm text-slate-500">No transactions in the last {TREND_MONTHS} months.</p>
      ) : (
        <div className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={data} margin={{ top: 4, right: 4, left: 0, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} />
              <XAxis dataKey="month" tickLine={false} axisLine={false} fontSize={12} />
              <YAxis tickFormatter={formatCompact} tickLine={false} axisLine={false} fontSize={12} width={44} />
              <Tooltip formatter={(value) => formatMoney(Number(value), currency)} />
              <Legend />
              <Bar dataKey="Income" fill="#10b981" radius={[4, 4, 0, 0]} />
              <Bar dataKey="Expenses" fill="#f43f5e" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}
    </Card>
  )
}