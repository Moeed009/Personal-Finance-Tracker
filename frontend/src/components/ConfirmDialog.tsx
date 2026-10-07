import type { ReactNode } from 'react'
import { Button } from '@/components/Button'
import { Modal } from '@/components/Modal'

interface ConfirmDialogProps {
  title: string
  message: ReactNode
  confirmLabel: string
  pendingLabel: string
  isPending: boolean
  error?: string
  onConfirm: () => void
  onClose: () => void
}

export function ConfirmDialog({
  title,
  message,
  confirmLabel,
  pendingLabel,
  isPending,
  error,
  onConfirm,
  onClose,
}: ConfirmDialogProps) {
  return (
    <Modal title={title} onClose={onClose}>
      <div className="text-sm text-slate-600">{message}</div>

      {error && <p className="mt-4 rounded-lg bg-rose-50 px-3 py-2 text-sm text-rose-700">{error}</p>}

      <div className="mt-6 flex justify-end gap-2">
        <Button variant="secondary" onClick={onClose}>
          Cancel
        </Button>
        <Button variant="danger" disabled={isPending} onClick={onConfirm}>
          {isPending ? pendingLabel : confirmLabel}
        </Button>
      </div>
    </Modal>
  )
}