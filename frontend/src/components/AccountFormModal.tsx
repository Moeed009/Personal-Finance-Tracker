import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { accountsApi } from '@/api/accounts'
import { Button } from '@/components/Button'
import { Modal } from '@/components/Modal'
import { SelectField } from '@/components/SelectField'
import { TextField } from '@/components/TextField'
import { ACCOUNTS_KEY } from '@/hooks/useAccounts'
import { ACCOUNT_TYPES, ACCOUNT_TYPE_LABELS } from '@/lib/constants'
import type { Account } from '@/types/api'

const schema = z.object({
  name: z.string().trim().min(1, 'Name is required').max(100, 'Maximum 100 characters'),
  type: z.enum(ACCOUNT_TYPES),
  opening_balance: z
    .string()
    .trim()
    .regex(/^-?\d{1,10}(\.\d{1,2})?$/, 'Enter a valid amount (up to 2 decimals)'),
})

type AccountFormValues = z.infer<typeof schema>

interface AccountFormModalProps {
  account: Account | null
  onClose: () => void
}

export function AccountFormModal({ account, onClose }: AccountFormModalProps) {
  const queryClient = useQueryClient()

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<AccountFormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      name: account?.name ?? '',
      type: account?.type ?? 'BANK',
      opening_balance: account?.opening_balance ?? '0.00',
    },
  })

  const mutation = useMutation({
    mutationFn: (values: AccountFormValues) =>
      account ? accountsApi.update(account.id, values) : accountsApi.create(values),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ACCOUNTS_KEY })
      onClose()
    },
  })

  return (
    <Modal title={account ? 'Edit account' : 'Add account'} onClose={onClose}>
      <form onSubmit={handleSubmit((values) => mutation.mutate(values))} className="space-y-4" noValidate>
        <TextField label="Account name" placeholder="e.g. HBL Savings" error={errors.name?.message} {...register('name')} />

        <SelectField label="Type" error={errors.type?.message} {...register('type')}>
          {ACCOUNT_TYPES.map((type) => (
            <option key={type} value={type}>
              {ACCOUNT_TYPE_LABELS[type]}
            </option>
          ))}
        </SelectField>

        <TextField
          label="Opening balance"
          inputMode="decimal"
          error={errors.opening_balance?.message}
          {...register('opening_balance')}
        />

        {mutation.error && (
          <p className="rounded-lg bg-rose-50 px-3 py-2 text-sm text-rose-700">{mutation.error.message}</p>
        )}

        <div className="flex justify-end gap-2 pt-2">
          <Button variant="secondary" onClick={onClose}>
            Cancel
          </Button>
          <Button type="submit" disabled={mutation.isPending}>
            {mutation.isPending ? 'Saving...' : account ? 'Save changes' : 'Create account'}
          </Button>
        </div>
      </form>
    </Modal>
  )
}