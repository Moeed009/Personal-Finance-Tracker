import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { budgetsApi } from '@/api/budgets'
import { Button } from '@/components/Button'
import { Modal } from '@/components/Modal'
import { SelectField } from '@/components/SelectField'
import { TextField } from '@/components/TextField'
import { useCategories } from '@/hooks/useCategories'
import { invalidateFinanceData } from '@/lib/invalidate'
import { monthLabel, monthStart } from '@/lib/months'
import { positiveAmount } from '@/lib/validation'
import type { Budget } from '@/types/api'

const schema = z.object({
  category_id: z.string().min(1, 'Select a category'),
  limit_amount: positiveAmount,
})

type FormValues = z.infer<typeof schema>

interface BudgetFormModalProps {
  month: string
  budget: Budget | null
  takenCategoryIds: string[]
  onClose: () => void
}

export function BudgetFormModal({ month, budget, takenCategoryIds, onClose }: BudgetFormModalProps) {
  const queryClient = useQueryClient()
  const categories = useCategories()

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      category_id: budget?.category_id ?? '',
      limit_amount: budget?.limit_amount ?? '',
    },
  })

  const mutation = useMutation({
    mutationFn: (values: FormValues) =>
      budget
        ? budgetsApi.update(budget.id, values.limit_amount)
        : budgetsApi.create({
            category_id: values.category_id,
            month: monthStart(month),
            limit_amount: values.limit_amount,
          }),
    onSuccess: async () => {
      await invalidateFinanceData(queryClient)
      onClose()
    },
  })

  const options = (categories.data ?? []).filter(
    (category) => category.type !== 'INCOME' && !takenCategoryIds.includes(category.id),
  )

  if (!budget && !categories.isPending && options.length === 0) {
    return (
      <Modal title="Add budget" onClose={onClose}>
        <p className="text-sm text-slate-600">
          Every expense category already has a budget for {monthLabel(month)}. Create a new category to add another.
        </p>
        <div className="mt-6 flex justify-end gap-2">
          <Button variant="secondary" onClick={onClose}>
            Close
          </Button>
          <Link
            to="/categories"
            className="inline-flex items-center justify-center rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700"
          >
            Go to categories
          </Link>
        </div>
      </Modal>
    )
  }

  return (
    <Modal title={budget ? 'Edit budget' : 'Add budget'} onClose={onClose}>
      <form onSubmit={handleSubmit((values) => mutation.mutate(values))} className="space-y-4" noValidate>
        <div>
          <p className="mb-1 text-sm font-medium text-slate-700">Month</p>
          <p className="text-sm text-slate-900">{monthLabel(month)}</p>
        </div>

        {budget ? (
          <div>
            <p className="mb-1 text-sm font-medium text-slate-700">Category</p>
            <p className="text-sm text-slate-900">{budget.category_name}</p>
          </div>
        ) : (
          <SelectField label="Category" error={errors.category_id?.message} {...register('category_id')}>
            <option value="">Select category</option>
            {options.map((category) => (
              <option key={category.id} value={category.id}>
                {category.name}
              </option>
            ))}
          </SelectField>
        )}

        <TextField
          label="Monthly limit"
          inputMode="decimal"
          placeholder="e.g. 20000"
          error={errors.limit_amount?.message}
          {...register('limit_amount')}
        />

        {mutation.error && (
          <p className="rounded-lg bg-rose-50 px-3 py-2 text-sm text-rose-700">{mutation.error.message}</p>
        )}

        <div className="flex justify-end gap-2 pt-2">
          <Button variant="secondary" onClick={onClose}>
            Cancel
          </Button>
          <Button type="submit" disabled={mutation.isPending}>
            {mutation.isPending ? 'Saving...' : budget ? 'Save changes' : 'Create budget'}
          </Button>
        </div>
      </form>
    </Modal>
  )
}