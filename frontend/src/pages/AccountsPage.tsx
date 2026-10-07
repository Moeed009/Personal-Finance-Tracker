import { useState } from 'react'
import { Banknote, Landmark, Pencil, Plus, Smartphone, Trash2, Wallet, type LucideIcon } from 'lucide-react'
import { AccountFormModal } from '@/components/AccountFormModal'
import { Button } from '@/components/Button'
import { DeleteAccountDialog } from '@/components/DeleteAccountDialog'
import { PageHeader } from '@/components/PageHeader'
import { useAuth } from '@/hooks/useAuth'
import { useAccounts } from '@/hooks/useAccounts'
import { ACCOUNT_TYPE_LABELS } from '@/lib/constants'
import { formatMoney } from '@/lib/format'
import type { Account, AccountType } from '@/types/api'

const typeIcons: Record<AccountType, LucideIcon> = {
  CASH: Banknote,
  BANK: Landmark,
  WALLET: Smartphone,
}

interface AccountCardProps {
  account: Account
  currency: string
  onEdit: () => void
  onDelete: () => void
}

function AccountCard({ account, currency, onEdit, onDelete }: AccountCardProps) {
  const Icon = typeIcons[account.type]
  const isNegative = Number(account.balance) < 0

  return (
    <div className="rounded-xl bg-white p-5 shadow-sm ring-1 ring-slate-200">
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-3">
          <span className="flex h-10 w-10 items-center justify-center rounded-lg bg-indigo-50 text-indigo-600">
            <Icon size={20} />
          </span>
          <div>
            <p className="font-medium text-slate-900">{account.name}</p>
            <p className="text-xs text-slate-500">{ACCOUNT_TYPE_LABELS[account.type]}</p>
          </div>
        </div>
        <div className="flex gap-1">
          <button
            onClick={onEdit}
            className="rounded-md p-2 text-slate-400 hover:bg-slate-100 hover:text-slate-700"
            aria-label={`Edit ${account.name}`}
          >
            <Pencil size={16} />
          </button>
          <button
            onClick={onDelete}
            className="rounded-md p-2 text-slate-400 hover:bg-rose-50 hover:text-rose-600"
            aria-label={`Delete ${account.name}`}
          >
            <Trash2 size={16} />
          </button>
        </div>
      </div>

      <p className={`mt-5 text-2xl font-semibold ${isNegative ? 'text-rose-600' : 'text-slate-900'}`}>
        {formatMoney(account.balance, currency)}
      </p>
      <p className="mt-1 text-xs text-slate-500">
        Opening balance: {formatMoney(account.opening_balance, currency)}
      </p>
    </div>
  )
}

function AccountsSkeleton() {
  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
      {[0, 1, 2].map((item) => (
        <div key={item} className="h-36 animate-pulse rounded-xl bg-slate-200" />
      ))}
    </div>
  )
}

export default function AccountsPage() {
  const { user } = useAuth()
  const currency = user?.currency ?? 'PKR'
  const { data, isLoading, error, refetch } = useAccounts()
  const [editing, setEditing] = useState<Account | 'new' | null>(null)
  const [deleting, setDeleting] = useState<Account | null>(null)

  return (
    <>
      <PageHeader
        title="Accounts"
        description="Your cash, bank accounts and wallets"
        actions={
          <Button onClick={() => setEditing('new')}>
            <Plus size={16} />
            Add account
          </Button>
        }
      />

      {isLoading && <AccountsSkeleton />}

      {error && (
        <div className="rounded-xl bg-rose-50 p-5 text-sm text-rose-700">
          <p>{error.message}</p>
          <Button variant="secondary" className="mt-3" onClick={() => refetch()}>
            Try again
          </Button>
        </div>
      )}

      {data && data.accounts.length === 0 && (
        <div className="rounded-xl border border-dashed border-slate-300 bg-white p-10 text-center">
          <Wallet className="mx-auto text-slate-400" size={32} />
          <p className="mt-3 font-medium text-slate-900">No accounts yet</p>
          <p className="mt-1 text-sm text-slate-500">Add your first account to start tracking transactions.</p>
          <Button className="mt-4" onClick={() => setEditing('new')}>
            <Plus size={16} />
            Add account
          </Button>
        </div>
      )}

      {data && data.accounts.length > 0 && (
        <>
          <div className="mb-6 rounded-xl bg-indigo-600 p-6 text-white shadow-sm">
            <p className="text-sm text-indigo-100">Total balance</p>
            <p className="mt-1 text-3xl font-semibold">{formatMoney(data.total_balance, currency)}</p>
            <p className="mt-1 text-xs text-indigo-200">Across {data.accounts.length} account(s)</p>
          </div>

          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {data.accounts.map((account) => (
              <AccountCard
                key={account.id}
                account={account}
                currency={currency}
                onEdit={() => setEditing(account)}
                onDelete={() => setDeleting(account)}
              />
            ))}
          </div>
        </>
      )}

      {editing && (
        <AccountFormModal account={editing === 'new' ? null : editing} onClose={() => setEditing(null)} />
      )}
      {deleting && <DeleteAccountDialog account={deleting} onClose={() => setDeleting(null)} />}
    </>
  )
}