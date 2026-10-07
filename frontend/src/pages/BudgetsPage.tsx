import { useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { PiggyBank, Plus } from 'lucide-react'
import { budgetsApi } from '@/api/budgets'
import { BudgetCard } from '@/components/BudgetCard'
import { BudgetFormModal } from '@/components/BudgetFormModal'
import { Button } from '@/components/Button'
import { ConfirmDialog } from '@/components/ConfirmDialog'
import { MonthSwitcher } from '@/components/MonthSwitcher'
import { PageHeader } from '@/components/PageHeader'
import { BUDGETS_KEY, useBudgets } from '@/hooks/useBudgets'
import { useAuth } from '@/hooks/useAuth'
import { formatMoney } from '@/lib/format'
import { currentMonth, isValidMonth, monthLabel } from '@/lib/months'
import type { Budget } from '@/types/api'

function DeleteBudgetDialog({ budget, onClose }: { budget: Budget; onClose: () => void }) {
  const queryClient = useQueryClient()

  const mutation = useMutation({
    mutationFn: () => budgetsApi.remove(budget.id),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: BUDGETS_KEY })
      onClose()
    },
  })

  return (
    <ConfirmDialog
      title="Delete budget"
      message={
        <>
          Delete the <span className="font-medium text-slate-900">{budget.category_name}</span> budget for{' '}
          {monthLabel(budget.month.slice(0, 7))}? Your transactions are not affected.
        </>
      }
      confirmLabel="Delete"
      pendingLabel="Deleting..."
      isPending={mutation.isPending}
      error={mutation.error?.message}
      onConfirm={() => mutation.mutate()}
      onClose={onClose}
    />
  )
}

export default function BudgetsPage() {
  const { user } = useAuth()
  const currency = user?.currency ?? 'PKR'

  const [searchParams, setSearchParams] = useSearchParams()
  const monthParam = searchParams.get('month')
  const month = isValidMonth(monthParam) ? monthParam : currentMonth()
  const setMonth = (next: string) => setSearchParams({ month: next }, { replace: true })

  const { data, isLoading, error, refetch } = useBudgets(month)
  const [editing, setEditing] = useState<Budget | 'new' | null>(null)
  const [deleting, setDeleting] = useState<Budget | null>(null)

  const totalLimit = (data ?? []).reduce((sum, budget) => sum + Number(budget.limit_amount), 0)
  const totalSpent = (data ?? []).reduce((sum, budget) => sum + Number(budget.spent), 0)
  const overallPercent = totalLimit > 0 ? (totalSpent / totalLimit) * 100 : 0

  return (
    <>
      <PageHeader
        title="Budgets"
        description="Set monthly spending limits for your categories"
        actions={
          <Button onClick={() => setEditing('new')}>
            <Plus size={16} />
            Add budget
          </Button>
        }
      />

      <MonthSwitcher month={month} onChange={setMonth} />

      {isLoading && (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {[0, 1, 2].map((item) => (
            <div key={item} className="h-36 animate-pulse rounded-xl bg-slate-200" />
          ))}
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

      {data && data.length === 0 && (
        <div className="rounded-xl border border-dashed border-slate-300 bg-white p-10 text-center">
          <PiggyBank className="mx-auto text-slate-400" size={32} />
          <p className="mt-3 font-medium text-slate-900">No budgets for {monthLabel(month)}</p>
          <p className="mt-1 text-sm text-slate-500">Add a budget to keep an eye on your spending.</p>
          <Button className="mt-4" onClick={() => setEditing('new')}>
            <Plus size={16} />
            Add budget
          </Button>
        </div>
      )}

      {data && data.length > 0 && (
        <>
          <div className="mb-6 rounded-xl bg-white p-6 shadow-sm ring-1 ring-slate-200">
            <div className="flex flex-wrap items-baseline justify-between gap-2">
              <p className="text-sm text-slate-500">Total spent this month</p>
              <p className="text-sm text-slate-500">{overallPercent.toFixed(0)}% of total budget</p>
            </div>
            <p className="mt-1 text-2xl font-semibold text-slate-900">
              {formatMoney(totalSpent, currency)}
              <span className="text-base font-normal text-slate-500"> of {formatMoney(totalLimit, currency)}</span>
            </p>
            <div className="mt-3 h-2 overflow-hidden rounded-full bg-slate-100">
              <div
                className={`h-full rounded-full ${overallPercent >= 100 ? 'bg-rose-500' : overallPercent >= 80 ? 'bg-amber-500' : 'bg-indigo-500'}`}
                style={{ width: `${Math.min(100, overallPercent)}%` }}
              />
            </div>
          </div>

          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {data.map((budget) => (
              <BudgetCard
                key={budget.id}
                budget={budget}
                currency={currency}
                onEdit={() => setEditing(budget)}
                onDelete={() => setDeleting(budget)}
              />
            ))}
          </div>
        </>
      )}

      {editing && (
        <BudgetFormModal
          month={month}
          budget={editing === 'new' ? null : editing}
          takenCategoryIds={(data ?? []).map((budget) => budget.category_id)}
          onClose={() => setEditing(null)}
        />
      )}
      {deleting && <DeleteBudgetDialog budget={deleting} onClose={() => setDeleting(null)} />}
    </>
  )
}