import { ArrowUpRight, PiggyBank, TrendingDown, TrendingUp, Wallet } from 'lucide-react'
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
import { useMonthParam } from '@/hooks/useMonthParam'
import { formatMoney } from '@/lib/format'
import { monthLabel } from '@/lib/months'

function greeting(): string {
  const hour = new Date().getHours()
  if (hour < 12) return 'Good morning'
  if (hour < 17) return 'Good afternoon'
  return 'Good evening'
}

function SavingsRing({ percent, overspent }: { percent: number; overspent: boolean }) {
  const shown = overspent ? 0 : Math.min(Math.max(percent, 0), 100)

  return (
    <div
      role="img"
      aria-label={overspent ? 'Spent more than earned' : `${percent.toFixed(0)} percent of income saved`}
      className="flex h-28 w-28 shrink-0 items-center justify-center rounded-full"
      style={{ background: `conic-gradient(#34d399 0 ${shown}%, rgba(255,255,255,0.07) ${shown}% 100%)` }}
    >
      <div className="flex h-[5.5rem] w-[5.5rem] flex-col items-center justify-center rounded-full bg-[#0e1714]">
        {overspent ? (
          <span className="font-display text-lg font-bold text-rose-700">Over</span>
        ) : (
          <span className="font-display text-2xl font-bold text-slate-900">{percent.toFixed(0)}%</span>
        )}
        <span className="text-[11px] text-slate-500">{overspent ? 'income' : 'of income'}</span>
      </div>
    </div>
  )
}

export default function DashboardPage() {
  const { user } = useAuth()
  const currency = user?.currency ?? 'PKR'
  const [month, setMonth] = useMonthParam()

  const summary = useMonthSummary(month)
  const accounts = useAccounts()

  const savings = summary.data ? Number(summary.data.savings) : 0
  const savingsRate = summary.data ? Number(summary.data.savings_rate_percent) : 0
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
              {summary.data && (
                <span
                  className={`inline-flex items-center gap-1.5 self-start rounded-full border px-3 py-1.5 text-xs font-bold ${
                    savings >= 0
                      ? 'border-emerald-500/30 bg-black/30 text-emerald-800'
                      : 'border-rose-400/40 bg-black/30 text-rose-700'
                  }`}
                >
                  <ArrowUpRight size={14} className={savings >= 0 ? '' : 'rotate-90'} />
                  {savings >= 0
                    ? `${formatMoney(savings, currency)} saved this month`
                    : `${formatMoney(Math.abs(savings), currency)} more spent than earned`}
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

        <section
          aria-label="Savings rate"
          className="card-lift animate-rise flex flex-col gap-5 rounded-3xl bg-white p-6 shadow-sm ring-1 ring-slate-200"
        >
          <div className="flex items-center justify-between">
            <h2 className="text-base font-semibold text-slate-700">Savings rate</h2>
            {summary.data && (
              <span
                className={`rounded-full px-2.5 py-1 text-xs font-bold ${
                  savings < 0
                    ? 'bg-rose-500/15 text-rose-700'
                    : savingsRate >= 20
                      ? 'bg-emerald-500/15 text-emerald-700'
                      : 'bg-amber-500/15 text-amber-700'
                }`}
              >
                {savings < 0 ? 'Overspent' : savingsRate >= 20 ? 'On track' : 'Below 20%'}
              </span>
            )}
          </div>
          {summary.isLoading ? (
            <div className="h-28 animate-pulse rounded-2xl bg-slate-100" />
          ) : (
            <div className="flex items-center gap-5">
              <SavingsRing percent={savingsRate} overspent={savings < 0} />
              <div className="flex flex-col gap-1.5">
                <span
                  className={`font-display text-xl font-semibold ${savings >= 0 ? 'text-slate-900' : 'text-rose-700'}`}
                >
                  {formatMoney(Math.abs(savings), currency)}
                </span>
                <span className="text-sm leading-relaxed text-slate-500">
                  {savings >= 0 ? 'saved from ' : 'more spent than '}
                  {summary.data ? formatMoney(summary.data.income, currency) : '—'} income
                </span>
              </div>
            </div>
          )}
        </section>
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
          label="Savings"
          icon={PiggyBank}
          tone={savings > 0 ? 'positive' : savings < 0 ? 'negative' : 'default'}
          isLoading={summary.isLoading}
          value={summary.data ? formatMoney(savings, currency) : undefined}
          hint={
            summary.data
              ? savings < 0
                ? 'Spent more than earned'
                : `${savingsRate.toFixed(0)}% of income saved`
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
