import type { ReactNode } from 'react'
import { ArrowLeftRight, Pencil, Trash2, Unlink } from 'lucide-react'
import { formatDay, formatMoney } from '@/lib/format'
import type { Account, Category, Transaction } from '@/types/api'

interface TransactionTableProps {
  items: Transaction[]
  accounts: Map<string, Account>
  categories: Map<string, Category>
  currency: string
  onEdit: (transaction: Transaction) => void
  onDelete: (transaction: Transaction) => void
  onNotTransfer?: (transaction: Transaction) => void
  onMarkTransfer?: (transaction: Transaction) => void
}

function Badge({ children, tone = 'default' }: { children: ReactNode; tone?: 'default' | 'transfer' }) {
  return (
    <span
      className={`rounded-full px-2 py-0.5 text-[11px] font-medium ${
        tone === 'transfer' ? 'bg-sky-500/15 text-sky-600' : 'bg-slate-100 text-slate-600'
      }`}
    >
      {children}
    </span>
  )
}

function categoryLabel(transaction: Transaction, categories: Map<string, Category>): string {
  if (transaction.transfer_group_id) return 'Own transfer'
  if (!transaction.category_id) return 'Uncategorized'
  return categories.get(transaction.category_id)?.name ?? 'Removed category'
}

function accountName(accounts: Map<string, Account>, id: string | undefined): string {
  return (id && accounts.get(id)?.name) || 'another account'
}

/** "Meezan → NayaPay" for a transfer, using the other leg when it is on this page. */
function transferRoute(transaction: Transaction, items: Transaction[], accounts: Map<string, Account>): string {
  const partner = items.find(
    (other) => other.id !== transaction.id && other.transfer_group_id === transaction.transfer_group_id,
  )
  const isOutgoing = transaction.type !== 'INCOME'
  const from = isOutgoing ? transaction.account_id : partner?.account_id
  const to = isOutgoing ? partner?.account_id : transaction.account_id

  if (!partner) {
    return isOutgoing
      ? `${accountName(accounts, from)} → other account`
      : `other account → ${accountName(accounts, to)}`
  }

  return `${accountName(accounts, from)} → ${accountName(accounts, to)}`
}

const iconButton = 'rounded-md p-2 text-slate-400 hover:bg-slate-100 hover:text-slate-700'

export function TransactionTable({
  items,
  accounts,
  categories,
  currency,
  onEdit,
  onDelete,
  onNotTransfer,
  onMarkTransfer,
}: TransactionTableProps) {
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
            const canMark =
              !isTransfer &&
              Boolean(transaction.import_batch_id) &&
              (transaction.type === 'INCOME' || transaction.type === 'EXPENSE')

            const amountTone = isTransfer ? 'text-sky-600' : isIncome ? 'text-emerald-600' : 'text-rose-600'

            return (
              <tr key={transaction.id} className="hover:bg-slate-50">
                <td className="whitespace-nowrap px-4 py-3 text-slate-600">{formatDay(transaction.transaction_date)}</td>
                <td className="px-4 py-3">
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="font-medium text-slate-900">{transaction.description}</span>
                    {isTransfer && <Badge tone="transfer">Transfer</Badge>}
                    {transaction.is_recurring && <Badge>Recurring</Badge>}
                    {transaction.import_batch_id && <Badge>Imported</Badge>}
                  </div>
                  {transaction.merchant && <p className="text-xs text-slate-500">{transaction.merchant}</p>}
                </td>
                <td className="px-4 py-3 text-slate-600">{categoryLabel(transaction, categories)}</td>
                <td className="px-4 py-3 text-slate-600">
                  {isTransfer ? (
                    <span className="inline-flex items-center gap-1.5 whitespace-nowrap">
                      <ArrowLeftRight size={13} className="text-sky-600" />
                      {transferRoute(transaction, items, accounts)}
                    </span>
                  ) : (
                    (accounts.get(transaction.account_id)?.name ?? '—')
                  )}
                </td>
                <td
                  className={`whitespace-nowrap px-4 py-3 text-right font-medium ${amountTone}`}
                  title={isTransfer ? 'Moved between your own accounts. Not counted as income or expense.' : undefined}
                >
                  {isIncome ? '+' : '−'}
                  {formatMoney(transaction.amount, currency)}
                </td>
                <td className="whitespace-nowrap px-4 py-3 text-right">
                  {canMark && onMarkTransfer && (
                    <button
                      onClick={() => onMarkTransfer(transaction)}
                      className={iconButton}
                      aria-label={`${transaction.description} is a transfer between my accounts`}
                      title="Mark as transfer between my own accounts"
                    >
                      <ArrowLeftRight size={16} />
                    </button>
                  )}
                  {!isTransfer && (
                    <button
                      onClick={() => onEdit(transaction)}
                      className={iconButton}
                      aria-label={`Edit ${transaction.description}`}
                    >
                      <Pencil size={16} />
                    </button>
                  )}
                  {isTransfer && transaction.import_batch_id && onNotTransfer && (
                    <button
                      onClick={() => onNotTransfer(transaction)}
                      className={iconButton}
                      aria-label={`${transaction.description} is not a transfer between my accounts`}
                      title="Not a transfer: count it as income or expense again"
                    >
                      <Unlink size={16} />
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
