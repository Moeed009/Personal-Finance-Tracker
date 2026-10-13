import { useMemo } from 'react'
import { Bar, BarChart, CartesianGrid, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { Card } from '@/components/Card'
import { TREND_MONTHS, useTrends } from '@/hooks/useInsights'
import { formatCompact, formatMoney } from '@/lib/format'
import { shortMonthLabel } from '@/lib/months'

const AXIS_TICK = { fill: '#8fa39a', fontSize: 12 }
const TOOLTIP_STYLE = {
  background: 'rgba(10, 18, 15, 0.95)',
  border: '1px solid rgba(255, 255, 255, 0.08)',
  borderRadius: 14,
  color: '#ecf3ef',
}

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
              <defs>
                <linearGradient id="income-bar" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#6ee7b7" />
                  <stop offset="100%" stopColor="#10b981" />
                </linearGradient>
                <linearGradient id="expense-bar" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#f5d68a" />
                  <stop offset="100%" stopColor="#c9952b" />
                </linearGradient>
              </defs>
              <CartesianGrid stroke="rgba(255,255,255,0.06)" strokeDasharray="3 3" vertical={false} />
              <XAxis dataKey="month" tickLine={false} axisLine={false} tick={AXIS_TICK} />
              <YAxis tickFormatter={formatCompact} tickLine={false} axisLine={false} tick={AXIS_TICK} width={44} />
              <Tooltip
                cursor={{ fill: 'rgba(255,255,255,0.04)' }}
                contentStyle={TOOLTIP_STYLE}
                labelStyle={{ color: '#ecf3ef', fontWeight: 600 }}
                formatter={(value) => formatMoney(Number(value), currency)}
              />
              <Legend wrapperStyle={{ color: '#b3c3bc', fontSize: 13 }} />
              <Bar dataKey="Income" fill="url(#income-bar)" radius={[8, 8, 3, 3]} />
              <Bar dataKey="Expenses" fill="url(#expense-bar)" radius={[8, 8, 3, 3]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}
    </Card>
  )
}