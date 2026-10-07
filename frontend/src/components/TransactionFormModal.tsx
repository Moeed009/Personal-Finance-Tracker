import { useForm, type FieldNamesMarkedBoolean } from 'react-hook-form'
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
import { useCategories } from '@/hooks/useCategories'
import { isCategoryCompatible } from '@/lib/categories'
import { TRANSACTION_TYPES, TRANSACTION_TYPE_LABELS } from '@/lib/constants'
import { todayISO } from '@/lib/dates'
import { invalidateFinanceData } from '@/lib/invalidate'
import { isoDate, positiveAmount } from '@/lib/validation'
import type { Transaction, TransactionPatch } from '@/types/api'

const schema = z.object({
  type: z.enum(TRANSACTION_TYPES),
  account_id: z.string().min(1, 'Select an account'),
  amount: positiveAmount,
  transaction_date: isoDate,
  description: z.string().trim().min(1, 'Description is required').max(300, 'Maximum 300 characters'),
  category_id: z.string(),
  merchant: z.string().trim().max(150, 'Maximum 150 characters'),
})

type FormValues = z.infer<typeof schema>
type DirtyFields = Partial<Readonly<FieldNamesMarkedBoolean<FormValues>>>

function buildPatch(values: FormValues, dirty: DirtyFields): TransactionPatch {
  const patch: TransactionPatch = {}
  if (dirty.type) patch.type = values.type
  if (dirty.account_id) patch.account_id = values.account_id
  if (dirty.amount) patch.amount = values.amount
  if (dirty.transaction_date) patch.transaction_date = values.transaction_date
  if (dirty.description) patch.description = values.description
  if (dirty.category_id) patch.category_id = values.category_id || null
  if (dirty.merchant) patch.merchant = values.merchant || null
  return patch
}

interface TransactionFormModalProps {
  transaction: Transaction | null
  onClose: () => void
}

export function TransactionFormModal({ transaction, onClose }: TransactionFormModalProps) {
  const queryClient = useQueryClient()
  const accounts = useAccounts()
  const categories = useCategories()
  const accountList = accounts.data?.accounts ?? []

  const {
    register,
    handleSubmit,
    watch,
    setValue,
    formState: { errors, dirtyFields },
  } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: transaction
      ? {
          type: transaction.type,
          account_id: transaction.account_id,
          amount: transaction.amount,
          transaction_date: transaction.transaction_date,
          description: transaction.description,
          category_id: transaction.category_id ?? '',
          merchant: transaction.merchant ?? '',
        }
      : {
          type: 'EXPENSE',
          account_id: accountList.length === 1 ? accountList[0].id : '',
          amount: '',
          transaction_date: todayISO(),
          description: '',
          category_id: '',
          merchant: '',
        },
  })

  const type = watch('type')
  const compatibleCategories = (categories.data ?? []).filter((category) => isCategoryCompatible(category, type))

  const mutation = useMutation({
    mutationFn: async (values: FormValues) => {
      if (!transaction) {
        await transactionsApi.create({
          account_id: values.account_id,
          type: values.type,
          amount: values.amount,
          transaction_date: values.transaction_date,
          description: values.description,
          category_id: values.category_id || null,
          merchant: values.merchant || null,
        })
        return
      }

      const patch = buildPatch(values, dirtyFields)
      if (Object.keys(patch).length > 0) await transactionsApi.update(transaction.id, patch)
    },
    onSuccess: async () => {
      await invalidateFinanceData(queryClient)
      onClose()
    },
  })

  if (!accounts.isPending && accountList.length === 0) {
    return (
      <Modal title="Add transaction" onClose={onClose}>
        <p className="text-sm text-slate-600">You need at least one account before adding transactions.</p>
        <div className="mt-6 flex justify-end gap-2">
          <Button variant="secondary" onClick={onClose}>
            Close
          </Button>
          <Link
            to="/accounts"
            className="inline-flex items-center justify-center rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700"
          >
            Create account
          </Link>
        </div>
      </Modal>
    )
  }

  return (
    <Modal title={transaction ? 'Edit transaction' : 'Add transaction'} size="lg" onClose={onClose}>
      <form onSubmit={handleSubmit((values) => mutation.mutate(values))} className="space-y-4" noValidate>
        <div className="grid gap-4 sm:grid-cols-2">
          <SelectField
            label="Type"
            error={errors.type?.message}
            {...register('type', { onChange: () => setValue('category_id', '', { shouldDirty: true }) })}
          >
            {TRANSACTION_TYPES.map((value) => (
              <option key={value} value={value}>
                {TRANSACTION_TYPE_LABELS[value]}
              </option>
            ))}
          </SelectField>

          <TextField label="Amount" inputMode="decimal" error={errors.amount?.message} {...register('amount')} />

          <SelectField label="Account" error={errors.account_id?.message} {...register('account_id')}>
            <option value="">Select account</option>
            {accountList.map((account) => (
              <option key={account.id} value={account.id}>
                {account.name}
              </option>
            ))}
          </SelectField>

          <TextField label="Date" type="date" error={errors.transaction_date?.message} {...register('transaction_date')} />
        </div>

        <TextField
          label="Description"
          placeholder="e.g. Foodpanda dinner"
          error={errors.description?.message}
          {...register('description')}
        />

        <SelectField label="Category" error={errors.category_id?.message} {...register('category_id')}>
          <option value="">{transaction ? 'Uncategorized' : 'Auto-detect from description'}</option>
          {compatibleCategories.map((category) => (
            <option key={category.id} value={category.id}>
              {category.name}
            </option>
          ))}
        </SelectField>

        <TextField
          label="Merchant (optional)"
          placeholder="Detected from description if left empty"
          error={errors.merchant?.message}
          {...register('merchant')}
        />

        {mutation.error && (
          <p className="rounded-lg bg-rose-50 px-3 py-2 text-sm text-rose-700">{mutation.error.message}</p>
        )}

        <div className="flex justify-end gap-2 pt-2">
          <Button variant="secondary" onClick={onClose}>
            Cancel
          </Button>
          <Button type="submit" disabled={mutation.isPending}>
            {mutation.isPending ? 'Saving...' : transaction ? 'Save changes' : 'Add transaction'}
          </Button>
        </div>
      </form>
    </Modal>
  )
}