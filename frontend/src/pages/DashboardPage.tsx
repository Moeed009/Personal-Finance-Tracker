import { CalendarClock, Gauge, Landmark, TrendingDown, TrendingUp, Wallet } from 'lucide-react'
import { BudgetStatusCard } from '@/components/BudgetStatusCard'
import { Button } from '@/components/Button'
import { MonthSwitcher } from '@/components/MonthSwitcher'
import { PageHeader } from '@/components/PageHeader'
import { RecentTransactionsCard } from '@/components/RecentTransactionsCard'
import { SpendingByCategoryCard } from '@/components/SpendingByCategoryCard'
import { StatCard } from '@/components/StatCard'
import { TrendsCard } from '@/components/TrendsCard'
import { UnusualSpendingCard } from '@/components/UnusualSpendingCard'
import { useAccounts } from '@/hooks/useAccounts'
import { useAuth } from '@/hooks/useAuth'
import { useMonthSummary } from '@/hooks/useInsights'
import { useRecurring } from '@/hooks/useRecurring'
import { useMonthParam } from '@/hooks/useMonthParam'
import { formatMoney } from '@/lib/format'
import { currentMonth, monthLabel, shiftMonth } from '@/lib/months'

function greeting(): string {
  const hour = new Date().getHours()
  if (hour < 12) return 'Good morning'
  if (hour < 17) return 'Good afternoon'
  return 'Good evening'
}

const UPCOMING_DAYS = 30

function isoDay(date: Date): string {
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`
}

/** Days of the month that have passed so far: all of them for past months, none for future ones. */
function daysElapsed(month: string): { elapsed: number; total: number } {
  const [year, monthNumber] = month.split('-').map(Number)
  const total = new Date(year, monthNumber, 0).getDate()
  const current = currentMonth()
  if (month < current) return { elapsed: total, total }
  if (month > current) return { elapsed: 0, total }
  return { elapsed: new Date().getDate(), total }
}

function SpendingPaceCard({ month, currency }: { month: string; currency: string }) {
  const summary = useMonthSummary(month)
  const previous = useMonthSummary(shiftMonth(month, -1))

  const spent = summary.data ? Number(summary.data.expense) : 0
  const lastMonth = previous.data ? Number(previous.data.expense) : 0
  const { elapsed, total } = daysElapsed(month)
  const isCurrent = month === currentMonth()
  const dailyAverage = elapsed > 0 ? spent / elapsed : 0
  const projected = isCurrent ? dailyAverage * total : spent
  const share = lastMonth > 0 ? (spent / lastMonth) * 100 : 0
  const change = lastMonth > 0 ? ((projected - lastMonth) / lastMonth) * 100 : null

  return (
    <section
      aria-label="Spending pace"
      className="card-lift animate-rise flex flex-col gap-5 rounded-3xl bg-white p-6 shadow-sm ring-1 ring-slate-200"
    >
      <div className="flex items-center justify-between gap-3">
        <h2 className="flex items-center gap-2 text-base font-semibold text-slate-700">
          <Gauge size={16} className="text-amber-700" />
          Spending pace
        </h2>
        {change !== null && summary.data && (
          <span
            className={`rounded-full px-2.5 py-1 text-xs font-bold ${
              change > 5
                ? 'bg-rose-500/15 text-rose-700'
                : change < -5
                  ? 'bg-emerald-500/15 text-emerald-700'
                  : 'bg-amber-500/15 text-amber-700'
            }`}
          >
            {Math.abs(change) < 1
              ? 'Same as last month'
              : `${Math.abs(change).toFixed(0)}% ${change > 0 ? 'above' : 'below'} last month`}
          </span>
        )}
      </div>

      {summary.isLoading || previous.isLoading ? (
        <div className="h-28 animate-pulse rounded-2xl bg-slate-100" />
      ) : (
        <>
          <div>
            <p className="font-display text-3xl font-bold tracking-tight text-slate-900">
              {formatMoney(dailyAverage.toFixed(2), currency)}
            </p>
            <p className="mt-1 text-sm text-slate-500">
              average spent per day{elapsed > 0 ? ` over ${elapsed} day${elapsed === 1 ? '' : 's'}` : ''}
            </p>
          </div>

          <div className="flex flex-col gap-2">
            <div
              className="h-2.5 overflow-hidden rounded-full bg-glass/10"
              role="img"
              aria-label={
                lastMonth > 0 ? `${share.toFixed(0)} percent of last month's spending used` : 'No spending last month'
              }
            >
              <div
                className={`h-full rounded-full ${share > 100 ? 'bg-rose-500' : 'bg-gradient-to-r from-emerald-500 to-amber-500'}`}
                style={{ width: `${Math.min(share, 100)}%` }}
              />
            </div>
            <div className="flex justify-between gap-3 text-xs text-slate-500">
              <span>
                {isCurrent ? 'On track for ' : 'Spent '}
                <b className="font-semibold text-slate-700">{formatMoney(projected.toFixed(2), currency)}</b>
              </span>
              <span>
                Last month <b className="font-semibold text-slate-700">{formatMoney(lastMonth.toFixed(2), currency)}</b>
              </span>
            </div>
          </div>
        </>
      )}
    </section>
  )
}

export default function DashboardPage() {
  const { user } = useAuth()
  const currency = user?.currency ?? 'PKR'
  const [month, setMonth] = useMonthParam()

  const summary = useMonthSummary(month)
  const accounts = useAccounts()

  const recurring = useRecurring()

  const today = new Date()
  const horizon = new Date(today.getFullYear(), today.getMonth(), today.getDate() + UPCOMING_DAYS)
  const upcoming = (recurring.data?.items ?? []).filter(
    (item) => item.status !== 'DISMISSED' && item.next_due_date >= isoDay(today) && item.next_due_date <= isoDay(horizon),
  )
  const upcomingTotal = upcoming.reduce((sum, item) => sum + Number(item.avg_amount), 0)
  const accountCount = accounts.data?.accounts.length ?? 0
  const firstName = user?.full_name.split(' ')[0] ?? ''
  const topAccounts = accounts.data?.accounts.slice(0, 4) ?? []

  return (
    <>
      <PageHeader
        title={`${greeting()}${firstName ? `, ${firstName}` : ''}`}
        description={`Here is where your money went in ${monthLabel(month)}.`}
      />

      <MonthSwitcher month={month} onChange={setMonth} />

      {summary.error && (
        <div className="mb-6 flex items-center justify-between gap-3 rounded-2xl bg-rose-50 p-4 text-sm text-rose-700">
          <p>{summary.error.message}</p>
          <Button variant="secondary" onClick={() => summary.refetch()}>
            Try again
          </Button>
        </div>
      )}

      <div className="grid gap-5 lg:grid-cols-3">
        <section aria-label="Total balance" className="hero-card animate-rise rounded-3xl p-7 lg:col-span-2">
          <div className="relative z-10 flex flex-wrap justify-between gap-7">
            <div className="flex min-w-60 flex-col gap-3">
              <span className="flex items-center gap-2 text-xs font-bold uppercase tracking-widest text-emerald-800">
                <Wallet size={14} />
                Total balance
              </span>
              {accounts.isLoading ? (
                <div className="h-11 w-56 animate-pulse rounded-xl bg-glass/10" />
              ) : (
                <span className="font-display text-4xl font-bold tracking-tight sm:text-5xl">
                  {accounts.data ? formatMoney(accounts.data.total_balance, currency) : '—'}
                </span>
              )}
              {accountCount > 0 && (
                <span className="inline-flex items-center gap-1.5 self-start rounded-full border border-emerald-500/30 bg-black/30 px-3 py-1.5 text-xs font-bold text-emerald-800">
                  <Landmark size={14} />
                  Across {accountCount} account{accountCount === 1 ? '' : 's'}
                </span>
              )}
            </div>

            {topAccounts.length > 0 && (
              <div className="grid w-full max-w-md grid-cols-2 gap-3 self-start">
                {topAccounts.map((account) => (
                  <div
                    key={account.id}
                    className="rounded-2xl border border-glass/10 bg-black/30 p-3.5 backdrop-blur-md"
                  >
                    <p className="truncate text-xs text-slate-600">{account.name}</p>
                    <p className="mt-1.5 truncate font-display text-lg font-semibold">
                      {formatMoney(account.balance, currency)}
                    </p>
                  </div>
                ))}
              </div>
            )}
          </div>
        </section>

        <SpendingPaceCard month={month} currency={currency} />
      </div>

      <div className="mt-5 grid gap-5 sm:grid-cols-3">
        <StatCard
          label="Income"
          icon={TrendingUp}
          tone="positive"
          isLoading={summary.isLoading}
          value={summary.data ? formatMoney(summary.data.income, currency) : undefined}
          hint="This month"
        />

        <StatCard
          label="Expenses"
          icon={TrendingDown}
          tone="negative"
          isLoading={summary.isLoading}
          value={summary.data ? formatMoney(summary.data.expense, currency) : undefined}
          hint="This month"
        />

        <StatCard
          label="Upcoming bills"
          icon={CalendarClock}
          isLoading={recurring.isLoading}
          value={recurring.data ? formatMoney(upcomingTotal.toFixed(2), currency) : undefined}
          hint={
            recurring.data
              ? upcoming.length > 0
                ? `${upcoming.length} recurring payment${upcoming.length === 1 ? '' : 's'} in the next ${UPCOMING_DAYS} days`
                : `Nothing due in the next ${UPCOMING_DAYS} days`
              : undefined
          }
        />
      </div>

      <div className="mt-6 grid gap-6 lg:grid-cols-2">
        <SpendingByCategoryCard month={month} currency={currency} />
        <TrendsCard currency={currency} />
      </div>

      <div className="mt-6 grid gap-6 lg:grid-cols-2">
        <BudgetStatusCard month={month} currency={currency} />
        <UnusualSpendingCard month={month} currency={currency} />
      </div>

      <div className="mt-6">
        <RecentTransactionsCard currency={currency} />
      </div>
    </>
  )
}
