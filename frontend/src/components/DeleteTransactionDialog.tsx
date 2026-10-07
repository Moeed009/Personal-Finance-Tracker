import { useMutation, useQueryClient } from '@tanstack/react-query'
import { transactionsApi } from '@/api/transactions'
import { ConfirmDialog } from '@/components/ConfirmDialog'
import { formatMoney } from '@/lib/format'
import { invalidateFinanceData } from '@/lib/invalidate'
import type { Transaction } from '@/types/api'

interface DeleteTransactionDialogProps {
  transaction: Transaction
  currency: string
  onClose: () => void
}

export function DeleteTransactionDialog({ transaction, currency, onClose }: DeleteTransactionDialogProps) {
  const queryClient = useQueryClient()

  const mutation = useMutation({
    mutationFn: () => transactionsApi.remove(transaction.id),
    onSuccess: async () => {
      await invalidateFinanceData(queryClient)
      onClose()
    },
  })

  return (
    <ConfirmDialog
      title="Delete transaction"
      message={
        <>
          <p>
            Delete <span className="font-medium text-slate-900">{transaction.description}</span> (
            {formatMoney(transaction.amount, currency)})? Your account balance will be updated.
          </p>
          {transaction.transfer_group_id && (
            <p className="mt-2 font-medium text-rose-700">
              This is part of a transfer. Both sides of the transfer will be deleted.
            </p>
          )}
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