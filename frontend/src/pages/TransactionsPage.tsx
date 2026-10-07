import { useCallback, useMemo, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { ArrowLeftRight, Plus, Receipt } from 'lucide-react'
import { Button } from '@/components/Button'
import { DeleteTransactionDialog } from '@/components/DeleteTransactionDialog'
import { PageHeader } from '@/components/PageHeader'
import { Pagination } from '@/components/Pagination'
import { TransactionFilterBar } from '@/components/TransactionFilterBar'
import { TransactionFormModal } from '@/components/TransactionFormModal'
import { TransactionTable } from '@/components/TransactionTable'
import { TransferFormModal } from '@/components/TransferFormModal'
import { useAccounts } from '@/hooks/useAccounts'
import { useAuth } from '@/hooks/useAuth'
import { useCategories } from '@/hooks/useCategories'
import { TRANSACTIONS_PAGE_SIZE, useTransactions } from '@/hooks/useTransactions'
import { hasActiveFilters, parseFilters, type FilterPatch } from '@/lib/transaction-filters'
import type { Transaction } from '@/types/api'

export default function TransactionsPage() {
  const { user } = useAuth()
  const currency = user?.currency ?? 'PKR'

  const [searchParams, setSearchParams] = useSearchParams()
  const filters = parseFilters(searchParams)
  const filtersActive = hasActiveFilters(filters)

  const [editing, setEditing] = useState<Transaction | 'new' | null>(null)
  const [transferOpen, setTransferOpen] = useState(false)
  const [deleting, setDeleting] = useState<Transaction | null>(null)

  const updateFilters = useCallback(
    (patch: FilterPatch) => {
      setSearchParams(
        (previous) => {
          const next = new URLSearchParams(previous)
          for (const [key, value] of Object.entries(patch)) {
            if (value) next.set(key, value)
            else next.delete(key)
          }
          if (!('page' in patch)) next.delete('page')
          return next
        },
        { replace: true },
      )
    },
    [setSearchParams],
  )

  const clearFilters = useCallback(() => setSearchParams({}, { replace: true }), [setSearchParams])

  const transactions = useTransactions(filters)
  const accounts = useAccounts()
  const categories = useCategories()

  const accountMap = useMemo(
    () => new Map((accounts.data?.accounts ?? []).map((account) => [account.id, account] as const)),
    [accounts.data],
  )
  const categoryMap = useMemo(
    () => new Map((categories.data ?? []).map((category) => [category.id, category] as const)),
    [categories.data],
  )

  const isLoading = transactions.isPending || accounts.isPending || categories.isPending
  const error = transactions.error ?? accounts.error ?? categories.error

  const retry = () => {
    void transactions.refetch()
    void accounts.refetch()
    void categories.refetch()
  }

  return (
    <>
      <PageHeader
        title="Transactions"
        description="All your income and expenses"
        actions={
          <>
            <Button variant="secondary" onClick={() => setTransferOpen(true)}>
              <ArrowLeftRight size={16} />
              Transfer
            </Button>
            <Button onClick={() => setEditing('new')}>
              <Plus size={16} />
              Add transaction
            </Button>
          </>
        }
      />

      <TransactionFilterBar
        filters={filters}
        accounts={accounts.data?.accounts ?? []}
        categories={categories.data ?? []}
        onChange={updateFilters}
        onClear={clearFilters}
      />

      {isLoading && (
        <div className="space-y-2">
          {[0, 1, 2, 3, 4].map((item) => (
            <div key={item} className="h-12 animate-pulse rounded-lg bg-slate-200" />
          ))}
        </div>
      )}

      {!isLoading && error && (
        <div className="rounded-xl bg-rose-50 p-5 text-sm text-rose-700">
          <p>{error.message}</p>
          <Button variant="secondary" className="mt-3" onClick={retry}>
            Try again
          </Button>
        </div>
      )}

      {!isLoading && !error && transactions.data && (
        <div className="overflow-hidden rounded-xl bg-white shadow-sm ring-1 ring-slate-200">
          {transactions.data.items.length === 0 ? (
            <div className="p-10 text-center">
              <Receipt className="mx-auto text-slate-400" size={32} />
              <p className="mt-3 font-medium text-slate-900">
                {filtersActive
                  ? 'No transactions match your filters'
                  : filters.page > 1
                    ? 'No transactions on this page'
                    : 'No transactions yet'}
              </p>
              <p className="mt-1 text-sm text-slate-500">
                {filtersActive ? 'Try changing or clearing the filters.' : 'Add your first transaction to get started.'}
              </p>
              {filters.page > 1 ? (
                <Button variant="secondary" className="mt-4" onClick={() => updateFilters({ page: '' })}>
                  Go to first page
                </Button>
              ) : (
                !filtersActive && (
                  <Button className="mt-4" onClick={() => setEditing('new')}>
                    <Plus size={16} />
                    Add transaction
                  </Button>
                )
              )}
            </div>
          ) : (
            <div className={transactions.isPlaceholderData ? 'opacity-60 transition-opacity' : ''}>
              <TransactionTable
                items={transactions.data.items}
                accounts={accountMap}
                categories={categoryMap}
                currency={currency}
                onEdit={setEditing}
                onDelete={setDeleting}
              />
              <Pagination
                page={transactions.data.page}
                pageSize={TRANSACTIONS_PAGE_SIZE}
                total={transactions.data.total}
                onPageChange={(page) => updateFilters({ page: String(page) })}
              />
            </div>
          )}
        </div>
      )}

      {editing && (
        <TransactionFormModal transaction={editing === 'new' ? null : editing} onClose={() => setEditing(null)} />
      )}
      {transferOpen && <TransferFormModal onClose={() => setTransferOpen(false)} />}
      {deleting && (
        <DeleteTransactionDialog transaction={deleting} currency={currency} onClose={() => setDeleting(null)} />
      )}
    </>
  )
}