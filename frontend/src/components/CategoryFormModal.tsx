import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { categoriesApi } from '@/api/categories'
import { Button } from '@/components/Button'
import { CategoryTypeBadge } from '@/components/CategoryTypeBadge'
import { Modal } from '@/components/Modal'
import { SelectField } from '@/components/SelectField'
import { TextField } from '@/components/TextField'
import { CATEGORIES_KEY } from '@/hooks/useCategories'
import { CATEGORY_TYPES, CATEGORY_TYPE_LABELS } from '@/lib/constants'
import type { Category } from '@/types/api'

const schema = z.object({
  name: z.string().trim().min(1, 'Name is required').max(80, 'Maximum 80 characters'),
  type: z.enum(CATEGORY_TYPES),
})

type CategoryFormValues = z.infer<typeof schema>

interface CategoryFormModalProps {
  category: Category | null
  onClose: () => void
}

export function CategoryFormModal({ category, onClose }: CategoryFormModalProps) {
  const queryClient = useQueryClient()

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<CategoryFormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      name: category?.name ?? '',
      type: category?.type ?? 'EXPENSE',
    },
  })

  const mutation = useMutation({
    mutationFn: (values: CategoryFormValues) =>
      category ? categoriesApi.rename(category.id, values.name) : categoriesApi.create(values),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: CATEGORIES_KEY })
      onClose()
    },
  })

  return (
    <Modal title={category ? 'Rename category' : 'Add category'} onClose={onClose}>
      <form onSubmit={handleSubmit((values) => mutation.mutate(values))} className="space-y-4" noValidate>
        <TextField label="Category name" placeholder="e.g. Groceries" error={errors.name?.message} {...register('name')} />

        {category ? (
          <div>
            <p className="mb-1 text-sm font-medium text-slate-700">Type</p>
            <CategoryTypeBadge type={category.type} />
            <p className="mt-1 text-xs text-slate-500">The type cannot be changed after creation.</p>
          </div>
        ) : (
          <SelectField label="Type" error={errors.type?.message} {...register('type')}>
            {CATEGORY_TYPES.map((type) => (
              <option key={type} value={type}>
                {CATEGORY_TYPE_LABELS[type]}
              </option>
            ))}
          </SelectField>
        )}

        {mutation.error && (
          <p className="rounded-lg bg-rose-50 px-3 py-2 text-sm text-rose-700">{mutation.error.message}</p>
        )}

        <div className="flex justify-end gap-2 pt-2">
          <Button variant="secondary" onClick={onClose}>
            Cancel
          </Button>
          <Button type="submit" disabled={mutation.isPending}>
            {mutation.isPending ? 'Saving...' : category ? 'Save changes' : 'Create category'}
          </Button>
        </div>
      </form>
    </Modal>
  )
}