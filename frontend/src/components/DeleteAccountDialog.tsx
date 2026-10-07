import { useMutation, useQueryClient } from '@tanstack/react-query'
import { accountsApi } from '@/api/accounts'
import { ApiError } from '@/api/client'
import { Button } from '@/components/Button'
import { Modal } from '@/components/Modal'
import type { Account } from '@/types/api'

interface DeleteAccountDialogProps {
  account: Account
  onClose: () => void
}

export function DeleteAccountDialog({ account, onClose }: DeleteAccountDialogProps) {
  const queryClient = useQueryClient()

  const mutation = useMutation({
    mutationFn: (force: boolean) => accountsApi.remove(account.id, force),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ predicate: (query) => query.queryKey[0] !== 'me' })
      onClose()
    },
  })

  const hasTransactions = mutation.error instanceof ApiError && mutation.error.status === 409

  return (
    <Modal title="Delete account" onClose={onClose}>
      <p className="text-sm text-slate-600">
        Are you sure you want to delete <span className="font-medium text-slate-900">{account.name}</span>? This
        cannot be undone.
      </p>

      {mutation.error && (
        <p className="mt-4 rounded-lg bg-rose-50 px-3 py-2 text-sm text-rose-700">{mutation.error.message}</p>
      )}

      <div className="mt-6 flex justify-end gap-2">
        <Button variant="secondary" onClick={onClose}>
          Cancel
        </Button>
        <Button variant="danger" disabled={mutation.isPending} onClick={() => mutation.mutate(hasTransactions)}>
          {mutation.isPending ? 'Deleting...' : hasTransactions ? 'Delete with all transactions' : 'Delete'}
        </Button>
      </div>
    </Modal>
  )
}