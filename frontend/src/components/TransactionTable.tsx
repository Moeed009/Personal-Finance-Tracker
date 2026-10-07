import type { ReactNode } from 'react'
import { Pencil, Trash2 } from 'lucide-react'
import { formatDay, formatMoney } from '@/lib/format'
import type { Account, Category, Transaction } from '@/types/api'

interface TransactionTableProps {
  items: Transaction[]
  accounts: Map<string, Account>
  categories: Map<string, Category>
  currency: string
  onEdit: (transaction: Transaction) => void
  onDelete: (transaction: Transaction) => void
}

function Badge({ children }: { children: ReactNode }) {
  return (
    <span className="rounded-full bg-slate-100 px-2 py-0.5 text-[11px] font-medium text-slate-600">{children}</span>
  )
}

function categoryLabel(transaction: Transaction, categories: Map<string, Category>): string {
  if (transaction.transfer_group_id) return '—'
  if (!transaction.category_id) return 'Uncategorized'
  return categories.get(transaction.category_id)?.name ?? 'Removed category'
}

export function TransactionTable({ items, accounts, categories, currency, onEdit, onDelete }: TransactionTableProps) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full min-w-[720px] text-left text-sm">
        <thead className="border-b border-slate-100 text-xs uppercase tracking-wide text-slate-500">
          <tr>
            <th className="px-4 py-3 font-medium">Date</th>
            <th className="px-4 py-3 font-medium">Description</th>
            <th className="px-4 py-3 font-medium">Category</th>
            <th className="px-4 py-3 font-medium">Account</th>
            <th className="px-4 py-3 text-right font-medium">Amount</th>
            <th className="px-4 py-3">
              <span className="sr-only">Actions</span>
            </th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100">
          {items.map((transaction) => {
            const isIncome = transaction.type === 'INCOME'
            const isTransfer = Boolean(transaction.transfer_group_id)

            return (
              <tr key={transaction.id} className="hover:bg-slate-50">
                <td className="whitespace-nowrap px-4 py-3 text-slate-600">{formatDay(transaction.transaction_date)}</td>
                <td className="px-4 py-3">
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="font-medium text-slate-900">{transaction.description}</span>
                    {isTransfer && <Badge>Transfer</Badge>}
                    {transaction.is_recurring && <Badge>Recurring</Badge>}
                    {transaction.import_batch_id && <Badge>Imported</Badge>}
                  </div>
                  {transaction.merchant && <p className="text-xs text-slate-500">{transaction.merchant}</p>}
                </td>
                <td className="px-4 py-3 text-slate-600">{categoryLabel(transaction, categories)}</td>
                <td className="px-4 py-3 text-slate-600">{accounts.get(transaction.account_id)?.name ?? '—'}</td>
                <td
                  className={`whitespace-nowrap px-4 py-3 text-right font-medium ${
                    isIncome ? 'text-emerald-600' : 'text-rose-600'
                  }`}
                >
                  {isIncome ? '+' : '−'}
                  {formatMoney(transaction.amount, currency)}
                </td>
                <td className="whitespace-nowrap px-4 py-3 text-right">
                  {!isTransfer && (
                    <button
                      onClick={() => onEdit(transaction)}
                      className="rounded-md p-2 text-slate-400 hover:bg-slate-100 hover:text-slate-700"
                      aria-label={`Edit ${transaction.description}`}
                    >
                      <Pencil size={16} />
                    </button>
                  )}
                  <button
                    onClick={() => onDelete(transaction)}
                    className="rounded-md p-2 text-slate-400 hover:bg-rose-50 hover:text-rose-600"
                    aria-label={`Delete ${transaction.description}`}
                  >
                    <Trash2 size={16} />
                  </button>
                </td>
              </tr>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}