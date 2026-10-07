import { Link } from 'react-router-dom'
import { Card } from '@/components/Card'
import { useTransactions } from '@/hooks/useTransactions'
import { formatDay, formatMoney } from '@/lib/format'
import type { TransactionFilters } from '@/lib/transaction-filters'

const LATEST: TransactionFilters = {
  search: '',
  type: '',
  account_id: '',
  category_id: '',
  date_from: '',
  date_to: '',
  page: 1,
}

const MAX_ITEMS = 5

export function RecentTransactionsCard({ currency }: { currency: string }) {
  const query = useTransactions(LATEST)
  const items = (query.data?.items ?? []).slice(0, MAX_ITEMS)

  return (
    <Card
      title="Recent transactions"
      isLoading={query.isLoading}
      error={query.error}
      onRetry={() => query.refetch()}
      action={
        <Link to="/transactions" className="text-sm font-medium text-indigo-600 hover:underline">
          View all
        </Link>
      }
    >
      {items.length === 0 ? (
        <p className="py-8 text-center text-sm text-slate-500">No transactions yet.</p>
      ) : (
        <ul className="divide-y divide-slate-100">
          {items.map((transaction) => {
            const isIncome = transaction.type === 'INCOME'
            return (
              <li key={transaction.id} className="flex items-center justify-between gap-3 py-3">
                <div className="min-w-0">
                  <p className="truncate text-sm font-medium text-slate-900">{transaction.description}</p>
                  <p className="text-xs text-slate-500">
                    {formatDay(transaction.transaction_date)}
                    {transaction.transfer_group_id ? ' · Transfer' : ''}
                  </p>
                </div>
                <p className={`shrink-0 text-sm font-medium ${isIncome ? 'text-emerald-600' : 'text-rose-600'}`}>
                  {isIncome ? '+' : '−'}
                  {formatMoney(transaction.amount, currency)}
                </p>
              </li>
            )
          })}
        </ul>
      )}
    </Card>
  )
}