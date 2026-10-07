import { useMemo, useState } from 'react'
import { Button } from '@/components/Button'
import { Modal } from '@/components/Modal'
import { Pagination } from '@/components/Pagination'
import { useCategories } from '@/hooks/useCategories'
import { IMPORT_TRANSACTIONS_PAGE_SIZE, useImportBatchTransactions } from '@/hooks/useImports'
import { formatDay, formatMoney } from '@/lib/format'
import type { ImportBatch } from '@/types/api'

interface ImportBatchTransactionsModalProps {
  batch: ImportBatch
  currency: string
  onClose: () => void
}

export function ImportBatchTransactionsModal({ batch, currency, onClose }: ImportBatchTransactionsModalProps) {
  const [page, setPage] = useState(1)
  const transactions = useImportBatchTransactions(batch.id, page)
  const categories = useCategories()

  const categoryMap = useMemo(
    () => new Map((categories.data ?? []).map((category) => [category.id, category.name] as const)),
    [categories.data],
  )

  return (
    <Modal title={batch.filename} size="xl" onClose={onClose}>
      {transactions.isPending && <div className="h-40 animate-pulse rounded-lg bg-slate-200" />}

      {transactions.error && (
        <div className="rounded-lg bg-rose-50 p-4 text-sm text-rose-700">
          <p>{transactions.error.message}</p>
          <Button variant="secondary" className="mt-3" onClick={() => transactions.refetch()}>
            Try again
          </Button>
        </div>
      )}

      {transactions.data &&
        (transactions.data.items.length === 0 ? (
          <p className="py-8 text-center text-sm text-slate-500">No transactions were imported from this file.</p>
        ) : (
          <div className="overflow-hidden rounded-lg ring-1 ring-slate-200">
            <div className={`overflow-x-auto ${transactions.isPlaceholderData ? 'opacity-60' : ''}`}>
              <table className="w-full min-w-[520px] text-left text-sm">
                <thead className="border-b border-slate-100 text-xs uppercase tracking-wide text-slate-500">
                  <tr>
                    <th className="px-4 py-3 font-medium">Date</th>
                    <th className="px-4 py-3 font-medium">Description</th>
                    <th className="px-4 py-3 font-medium">Category</th>
                    <th className="px-4 py-3 text-right font-medium">Amount</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {transactions.data.items.map((transaction) => {
                    const isIncome = transaction.type === 'INCOME'
                    return (
                      <tr key={transaction.id}>
                        <td className="whitespace-nowrap px-4 py-3 text-slate-600">
                          {formatDay(transaction.transaction_date)}
                        </td>
                        <td className="px-4 py-3 font-medium text-slate-900">{transaction.description}</td>
                        <td className="px-4 py-3 text-slate-600">
                          {transaction.category_id
                            ? (categoryMap.get(transaction.category_id) ?? 'Removed category')
                            : 'Uncategorized'}
                        </td>
                        <td
                          className={`whitespace-nowrap px-4 py-3 text-right font-medium ${
                            isIncome ? 'text-emerald-600' : 'text-rose-600'
                          }`}
                        >
                          {isIncome ? '+' : '−'}
                          {formatMoney(transaction.amount, currency)}
                        </td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>
            <Pagination
              page={transactions.data.page}
              pageSize={IMPORT_TRANSACTIONS_PAGE_SIZE}
              total={transactions.data.total}
              onPageChange={setPage}
            />
          </div>
        ))}
    </Modal>
  )
}