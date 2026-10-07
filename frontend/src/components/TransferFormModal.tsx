import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { transactionsApi } from '@/api/transactions'
import { Button } from '@/components/Button'
import { Modal } from '@/components/Modal'
import { SelectField } from '@/components/SelectField'
import { TextField } from '@/components/TextField'
import { useAccounts } from '@/hooks/useAccounts'
import { todayISO } from '@/lib/dates'
import { invalidateFinanceData } from '@/lib/invalidate'
import { isoDate, positiveAmount } from '@/lib/validation'

const schema = z
  .object({
    from_account_id: z.string().min(1, 'Select the source account'),
    to_account_id: z.string().min(1, 'Select the destination account'),
    amount: positiveAmount,
    transaction_date: isoDate,
    description: z.string().trim().min(1, 'Description is required').max(300, 'Maximum 300 characters'),
  })
  .refine((data) => data.from_account_id !== data.to_account_id, {
    message: 'Accounts must be different',
    path: ['to_account_id'],
  })

type FormValues = z.infer<typeof schema>

export function TransferFormModal({ onClose }: { onClose: () => void }) {
  const queryClient = useQueryClient()
  const accounts = useAccounts()
  const accountList = accounts.data?.accounts ?? []

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      from_account_id: '',
      to_account_id: '',
      amount: '',
      transaction_date: todayISO(),
      description: 'Transfer',
    },
  })

  const mutation = useMutation({
    mutationFn: transactionsApi.transfer,
    onSuccess: async () => {
      await invalidateFinanceData(queryClient)
      onClose()
    },
  })

  if (!accounts.isPending && accountList.length < 2) {
    return (
      <Modal title="Transfer money" onClose={onClose}>
        <p className="text-sm text-slate-600">You need at least two accounts to make a transfer.</p>
        <div className="mt-6 flex justify-end gap-2">
          <Button variant="secondary" onClick={onClose}>
            Close
          </Button>
          <Link
            to="/accounts"
            className="inline-flex items-center justify-center rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700"
          >
            Go to accounts
          </Link>
        </div>
      </Modal>
    )
  }

  return (
    <Modal title="Transfer money" size="lg" onClose={onClose}>
      <form onSubmit={handleSubmit((values) => mutation.mutate(values))} className="space-y-4" noValidate>
        <div className="grid gap-4 sm:grid-cols-2">
          <SelectField label="From account" error={errors.from_account_id?.message} {...register('from_account_id')}>
            <option value="">Select account</option>
            {accountList.map((account) => (
              <option key={account.id} value={account.id}>
                {account.name}
              </option>
            ))}
          </SelectField>

          <SelectField label="To account" error={errors.to_account_id?.message} {...register('to_account_id')}>
            <option value="">Select account</option>
            {accountList.map((account) => (
              <option key={account.id} value={account.id}>
                {account.name}
              </option>
            ))}
          </SelectField>

          <TextField label="Amount" inputMode="decimal" error={errors.amount?.message} {...register('amount')} />
          <TextField label="Date" type="date" error={errors.transaction_date?.message} {...register('transaction_date')} />
        </div>

        <TextField label="Description" error={errors.description?.message} {...register('description')} />

        {mutation.error && (
          <p className="rounded-lg bg-rose-50 px-3 py-2 text-sm text-rose-700">{mutation.error.message}</p>
        )}

        <div className="flex justify-end gap-2 pt-2">
          <Button variant="secondary" onClick={onClose}>
            Cancel
          </Button>
          <Button type="submit" disabled={mutation.isPending}>
            {mutation.isPending ? 'Transferring...' : 'Transfer'}
          </Button>
        </div>
      </form>
    </Modal>
  )
}