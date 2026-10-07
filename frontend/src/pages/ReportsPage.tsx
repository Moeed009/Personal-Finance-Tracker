import { Download, Printer, PiggyBank, TrendingDown, TrendingUp } from 'lucide-react'
import { Button } from '@/components/Button'
import { Card } from '@/components/Card'
import { MonthSwitcher } from '@/components/MonthSwitcher'
import { PageHeader } from '@/components/PageHeader'
import { StatCard } from '@/components/StatCard'
import { useAuth } from '@/hooks/useAuth'
import { useMonthParam } from '@/hooks/useMonthParam'
import { useMonthlyReport } from '@/hooks/useReports'
import { downloadTextFile } from '@/lib/download'
import { formatDay, formatMoney } from '@/lib/format'
import { monthLabel } from '@/lib/months'
import { FREQUENCY_LABELS } from '@/lib/recurring'
import { reportToCsv } from '@/lib/report-csv'
import type { BudgetStatus, MonthlyReport, RecurringStatus } from '@/types/api'

const budgetBadges: Record<BudgetStatus, { label: string; className: string }> = {
  ON_TRACK: { label: 'On track', className: 'bg-emerald-50 text-emerald-700' },
  WARNING: { label: 'Warning', className: 'bg-amber-50 text-amber-700' },
  EXCEEDED: { label: 'Exceeded', className: 'bg-rose-50 text-rose-700' },
}

const recurringBadges: Record<Exclude<RecurringStatus, 'DISMISSED'>, string> = {
  DETECTED: 'bg-amber-50 text-amber-700',
  CONFIRMED: 'bg-emerald-50 text-emerald-700',
}

function Empty({ children }: { children: string }) {
  return <p className="py-6 text-center text-sm text-slate-500">{children}</p>
}

function CategoriesTable({ report, currency }: { report: MonthlyReport; currency: string }) {
  if (report.categories.length === 0) return <Empty>No expenses recorded this month.</Empty>

  return (
    <div className="overflow-x-auto">
      <table className="w-full min-w-[420px] text-left text-sm">
        <thead className="border-b border-slate-100 text-xs uppercase tracking-wide text-slate-500">
          <tr>
            <th className="py-2 font-medium">Category</th>
            <th className="py-2 font-medium">Share</th>
            <th className="py-2 text-right font-medium">Amount</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100">
          {report.categories.map((item) => {
            const percentage = Number(item.percentage)
            return (
              <tr key={item.category_id ?? item.category_name}>
                <td className="py-3 font-medium text-slate-900">{item.category_name}</td>
                <td className="py-3">
                  <div className="flex items-center gap-2">
                    <div className="h-1.5 w-24 overflow-hidden rounded-full bg-slate-100">
                      <div className="h-full rounded-full bg-indigo-500" style={{ width: `${Math.min(100, percentage)}%` }} />
                    </div>
                    <span className="text-xs text-slate-500">{percentage.toFixed(0)}%</span>
                  </div>
                </td>
                <td className="py-3 text-right text-slate-900">{formatMoney(item.total, currency)}</td>
              </tr>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}

function BudgetsTable({ report, currency }: { report: MonthlyReport; currency: string }) {
  if (report.budgets.length === 0) return <Empty>No budgets were set for this month.</Empty>

  return (
    <div className="overflow-x-auto">
      <table className="w-full min-w-[560px] text-left text-sm">
        <thead className="border-b border-slate-100 text-xs uppercase tracking-wide text-slate-500">
          <tr>
            <th className="py-2 font-medium">Category</th>
            <th className="py-2 text-right font-medium">Limit</th>
            <th className="py-2 text-right font-medium">Spent</th>
            <th className="py-2 text-right font-medium">Remaining</th>
            <th className="py-2 text-right font-medium">Status</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100">
          {report.budgets.map((budget) => {
            const badge = budgetBadges[budget.status]
            const isOver = Number(budget.remaining) < 0
            return (
              <tr key={budget.id}>
                <td className="py-3 font-medium text-slate-900">{budget.category_name}</td>
                <td className="py-3 text-right text-slate-600">{formatMoney(budget.limit_amount, currency)}</td>
                <td className="py-3 text-right text-slate-900">{formatMoney(budget.spent, currency)}</td>
                <td className={`py-3 text-right ${isOver ? 'text-rose-600' : 'text-slate-600'}`}>
                  {formatMoney(budget.remaining, currency)}
                </td>
                <td className="py-3 text-right">
                  <span className={`rounded-full px-2.5 py-0.5 text-xs font-medium ${badge.className}`}>{badge.label}</span>
                </td>
              </tr>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}

function RecurringTable({ report, currency }: { report: MonthlyReport; currency: string }) {
  if (report.recurring.length === 0) return <Empty>No recurring payments found.</Empty>

  return (
    <>
      <div className="overflow-x-auto">
        <table className="w-full min-w-[560px] text-left text-sm">
          <thead className="border-b border-slate-100 text-xs uppercase tracking-wide text-slate-500">
            <tr>
              <th className="py-2 font-medium">Payment</th>
              <th className="py-2 font-medium">Frequency</th>
              <th className="py-2 font-medium">Next due</th>
              <th className="py-2 text-right font-medium">Amount</th>
              <th className="py-2 text-right font-medium">Status</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {report.recurring.map((item) => (
              <tr key={item.id}>
                <td className="py-3 font-medium capitalize text-slate-900">{item.merchant}</td>
                <td className="py-3 text-slate-600">{FREQUENCY_LABELS[item.frequency]}</td>
                <td className="py-3 text-slate-600">{formatDay(item.next_due_date)}</td>
                <td className="py-3 text-right text-slate-900">{formatMoney(item.avg_amount, currency)}</td>
                <td className="py-3 text-right">
                  <span
                    className={`rounded-full px-2.5 py-0.5 text-xs font-medium ${
                      item.status === 'DISMISSED' ? 'bg-slate-100 text-slate-600' : recurringBadges[item.status]
                    }`}
                  >
                    {item.status === 'DETECTED' ? 'Needs review' : 'Confirmed'}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="mt-3 text-right text-sm text-slate-600">
        Estimated monthly cost:{' '}
        <span className="font-semibold text-slate-900">{formatMoney(report.recurring_monthly_cost, currency)}</span>
      </p>
    </>
  )
}

export default function ReportsPage() {
  const { user } = useAuth()
  const currency = user?.currency ?? 'PKR'
  const [month, setMonth] = useMonthParam()
  const { data, isLoading, error, refetch } = useMonthlyReport(month)

  const handleDownload = () => {
    if (data) downloadTextFile(`report-${month}.csv`, reportToCsv(data), 'text/csv;charset=utf-8')
  }

  const income = data ? Number(data.income) : 0
  const savings = data ? Number(data.savings) : 0
  const savingsRate = income > 0 ? `${((savings / income) * 100).toFixed(0)}% of income saved` : undefined

  return (
    <>
      <PageHeader
        title="Monthly report"
        description={`${monthLabel(month)}${user ? ` · ${user.full_name}` : ''}`}
        actions={
          <>
            <Button variant="secondary" className="print:hidden" disabled={!data} onClick={() => window.print()}>
              <Printer size={16} />
              Print / PDF
            </Button>
            <Button className="print:hidden" disabled={!data} onClick={handleDownload}>
              <Download size={16} />
              Download CSV
            </Button>
          </>
        }
      />

      <div className="print:hidden">
        <MonthSwitcher month={month} onChange={setMonth} />
      </div>

      {isLoading && (
        <div className="space-y-4">
          <div className="grid gap-4 sm:grid-cols-3">
            {[0, 1, 2].map((item) => (
              <div key={item} className="h-28 animate-pulse rounded-xl bg-slate-200" />
            ))}
          </div>
          <div className="h-48 animate-pulse rounded-xl bg-slate-200" />
        </div>
      )}

      {error && (
        <div className="rounded-xl bg-rose-50 p-5 text-sm text-rose-700">
          <p>{error.message}</p>
          <Button variant="secondary" className="mt-3" onClick={() => refetch()}>
            Try again
          </Button>
        </div>
      )}

      {data && (
        <div className="space-y-6">
          <div className="grid gap-4 sm:grid-cols-3">
            <StatCard label="Income" icon={TrendingUp} tone="positive" value={formatMoney(data.income, currency)} />
            <StatCard label="Expenses" icon={TrendingDown} tone="negative" value={formatMoney(data.expense, currency)} />
            <StatCard
              label="Savings"
              icon={PiggyBank}
              tone={savings < 0 ? 'negative' : savings > 0 ? 'positive' : 'default'}
              value={formatMoney(data.savings, currency)}
              hint={savingsRate}
            />
          </div>

          <Card title="Spending by category">
            <CategoriesTable report={data} currency={currency} />
          </Card>

          <Card title="Budgets">
            <BudgetsTable report={data} currency={currency} />
          </Card>

          <Card title="Recurring payments">
            <RecurringTable report={data} currency={currency} />
          </Card>
        </div>
      )}
    </>
  )
}