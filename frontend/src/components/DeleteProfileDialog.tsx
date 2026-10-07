import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { usersApi } from '@/api/users'
import { Button } from '@/components/Button'
import { Modal } from '@/components/Modal'
import { TextField } from '@/components/TextField'
import { ME_KEY } from '@/lib/auth-context'

const CONFIRM_WORD = 'DELETE'

export function DeleteProfileDialog({ onClose }: { onClose: () => void }) {
  const queryClient = useQueryClient()
  const [text, setText] = useState('')

  const mutation = useMutation({
    mutationFn: () => usersApi.remove(),
    onSuccess: () => {
      queryClient.removeQueries({ predicate: (query) => query.queryKey[0] !== ME_KEY[0] })
      queryClient.setQueryData(ME_KEY, null)
    },
  })

  return (
    <Modal title="Delete your account" onClose={onClose}>
      <div className="space-y-3 text-sm text-slate-600">
        <p>
          Your account will be scheduled for deletion and you will be logged out. If you log in again within the
          grace period (set by the server, 2 hours by default), the account is restored.
        </p>
        <p className="font-medium text-rose-700">
          After the grace period, all your accounts, transactions, budgets and files are permanently deleted.
        </p>
      </div>

      <div className="mt-4">
        <TextField
          label={`Type ${CONFIRM_WORD} to confirm`}
          value={text}
          onChange={(event) => setText(event.target.value)}
          autoComplete="off"
        />
      </div>

      {mutation.error && (
        <p className="mt-4 rounded-lg bg-rose-50 px-3 py-2 text-sm text-rose-700">{mutation.error.message}</p>
      )}

      <div className="mt-6 flex justify-end gap-2">
        <Button variant="secondary" onClick={onClose}>
          Cancel
        </Button>
        <Button variant="danger" disabled={text !== CONFIRM_WORD || mutation.isPending} onClick={() => mutation.mutate()}>
          {mutation.isPending ? 'Deleting...' : 'Delete my account'}
        </Button>
      </div>
    </Modal>
  )
}