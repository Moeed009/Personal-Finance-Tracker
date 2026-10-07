import { PiggyBank, TrendingDown, TrendingUp, Wallet } from 'lucide-react'
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

export default function DashboardPage() {
  const { user } = useAuth()
  const currency = user?.currency ?? 'PKR'
  const [month, setMonth] = useMonthParam()

  const summary = useMonthSummary(month)
  const accounts = useAccounts()

  const savings = summary.data ? Math.max(Number(summary.data.savings), 0) : 0
  const savingsRate = summary.data
    ? Math.max(Number(summary.data.savings_rate_percent), 0)
    : 0

  return (
    <>
      <PageHeader title="Dashboard" description={`Welcome back, ${user?.full_name}`} />

      <MonthSwitcher month={month} onChange={setMonth} />

      {summary.error && (
        <div className="mb-6 flex items-center justify-between gap-3 rounded-xl bg-rose-50 p-4 text-sm text-rose-700">
          <p>{summary.error.message}</p>
          <Button variant="secondary" onClick={() => summary.refetch()}>
            Try again
          </Button>
        </div>
      )}

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard
          label="Total balance"
          icon={Wallet}
          isLoading={accounts.isLoading}
          value={accounts.data ? formatMoney(accounts.data.total_balance, currency) : undefined}
          hint="Across all accounts"
        />

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
          tone={savings > 0 ? 'positive' : 'default'}
          isLoading={summary.isLoading}
          value={summary.data ? formatMoney(savings, currency) : undefined}
          hint={summary.data ? `${savingsRate.toFixed(0)}% of income saved` : undefined}
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
