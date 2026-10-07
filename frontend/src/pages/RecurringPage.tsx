import { useMemo, useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { Repeat, RefreshCw } from 'lucide-react'
import { recurringApi } from '@/api/recurring'
import { Button } from '@/components/Button'
import { PageHeader } from '@/components/PageHeader'
import { RecurringCard } from '@/components/RecurringCard'
import { useAccounts } from '@/hooks/useAccounts'
import { useAuth } from '@/hooks/useAuth'
import { useCategories } from '@/hooks/useCategories'
import { useRecurring } from '@/hooks/useRecurring'
import { formatMoney } from '@/lib/format'
import { invalidateFinanceData } from '@/lib/invalidate'

type Tab = 'ACTIVE' | 'DISMISSED'

export default function RecurringPage() {
  const { user } = useAuth()
  const currency = user?.currency ?? 'PKR'
  const queryClient = useQueryClient()

  const recurring = useRecurring()
  const accounts = useAccounts()
  const categories = useCategories()
  const [tab, setTab] = useState<Tab>('ACTIVE')

  const detect = useMutation({
    mutationFn: recurringApi.detect,
    onSuccess: () => invalidateFinanceData(queryClient),
  })

  const accountNames = useMemo(
    () => new Map((accounts.data?.accounts ?? []).map((account) => [account.id, account.name] as const)),
    [accounts.data],
  )
  const categoryNames = useMemo(
    () => new Map((categories.data ?? []).map((category) => [category.id, category.name] as const)),
    [categories.data],
  )

  const items = recurring.data?.items ?? []
  const active = items.filter((item) => item.status !== 'DISMISSED')
  const dismissed = items.filter((item) => item.status === 'DISMISSED')
  const needsReview = active.filter((item) => item.status === 'DETECTED').length
  const shown = tab === 'ACTIVE' ? active : dismissed

  const tabs: { value: Tab; label: string; count: number }[] = [
    { value: 'ACTIVE', label: 'Active', count: active.length },
    { value: 'DISMISSED', label: 'Dismissed', count: dismissed.length },
  ]

  return (
    <>
      <PageHeader
        title="Recurring"
        description="Subscriptions and regular payments found in your expenses"
        actions={
          <Button onClick={() => detect.mutate()} disabled={detect.isPending}>
            <RefreshCw size={16} className={detect.isPending ? 'animate-spin' : ''} />
            {detect.isPending ? 'Detecting...' : 'Detect recurring'}
          </Button>
        }
      />

      {detect.error && (
        <p className="mb-4 rounded-lg bg-rose-50 px-3 py-2 text-sm text-rose-700">{detect.error.message}</p>
      )}
      {detect.data && (
        <p className="mb-4 rounded-lg bg-emerald-50 px-3 py-2 text-sm text-emerald-700">
          {detect.data.detected === 0
            ? 'No recurring payments found yet.'
            : `Detection finished: ${detect.data.detected} recurring payment${detect.data.detected === 1 ? '' : 's'} found.`}
        </p>
      )}

      {recurring.isLoading && (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {[0, 1, 2].map((item) => (
            <div key={item} className="h-44 animate-pulse rounded-xl bg-slate-200" />
          ))}
        </div>
      )}

      {recurring.error && (
        <div className="rounded-xl bg-rose-50 p-5 text-sm text-rose-700">
          <p>{recurring.error.message}</p>
          <Button variant="secondary" className="mt-3" onClick={() => recurring.refetch()}>
            Try again
          </Button>
        </div>
      )}

      {recurring.data && (
        <>
          <div className="mb-6 rounded-xl bg-indigo-600 p-6 text-white shadow-sm">
            <p className="text-sm text-indigo-100">Estimated monthly cost</p>
            <p className="mt-1 text-3xl font-semibold">{formatMoney(recurring.data.total_monthly_cost, currency)}</p>
            <p className="mt-1 text-xs text-indigo-200">
              {active.length} active payment{active.length === 1 ? '' : 's'}
              {needsReview > 0 ? ` · ${needsReview} waiting for review` : ''}
            </p>
          </div>

          <div className="mb-6 inline-flex rounded-lg bg-slate-100 p-1">
            {tabs.map(({ value, label, count }) => (
              <button
                key={value}
                onClick={() => setTab(value)}
                className={`rounded-md px-4 py-1.5 text-sm font-medium transition ${
                  tab === value ? 'bg-white text-slate-900 shadow-sm' : 'text-slate-500 hover:text-slate-700'
                }`}
              >
                {label} ({count})
              </button>
            ))}
          </div>

          {shown.length === 0 ? (
            <div className="rounded-xl border border-dashed border-slate-300 bg-white p-10 text-center">
              <Repeat className="mx-auto text-slate-400" size={32} />
              {tab === 'ACTIVE' ? (
                <>
                  <p className="mt-3 font-medium text-slate-900">No recurring payments yet</p>
                  <p className="mx-auto mt-1 max-w-md text-sm text-slate-500">
                    A payment is detected when the same merchant appears at least 3 times with a regular gap (weekly,
                    every 2 weeks or monthly) and a similar amount. Run detection after adding or importing
                    transactions.
                  </p>
                </>
              ) : (
                <p className="mt-3 font-medium text-slate-900">Nothing dismissed</p>
              )}
            </div>
          ) : (
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {shown.map((item) => (
                <RecurringCard
                  key={item.id}
                  item={item}
                  accountName={accountNames.get(item.account_id) ?? '—'}
                  categoryName={item.category_id ? (categoryNames.get(item.category_id) ?? 'Removed category') : 'Uncategorized'}
                  currency={currency}
                />
              ))}
            </div>
          )}

          {tab === 'ACTIVE' && active.length > 0 && (
            <p className="mt-6 text-xs text-slate-500">
              Due dates are calculated from your latest payment. Run detection again after new payments to refresh them.
            </p>
          )}
        </>
      )}
    </>
  )
}