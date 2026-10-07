import { useState, type ReactNode } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { Pencil, Plus, Trash2 } from 'lucide-react'
import { categoriesApi } from '@/api/categories'
import { Button } from '@/components/Button'
import { CategoryFormModal } from '@/components/CategoryFormModal'
import { CategoryTypeBadge } from '@/components/CategoryTypeBadge'
import { ConfirmDialog } from '@/components/ConfirmDialog'
import { PageHeader } from '@/components/PageHeader'
import { CATEGORIES_KEY, useCategories } from '@/hooks/useCategories'
import { isCategoryCompatible } from '@/lib/categories'
import type { Category, TransactionType } from '@/types/api'

type Filter = 'ALL' | TransactionType

const filters: { value: Filter; label: string }[] = [
  { value: 'ALL', label: 'All' },
  { value: 'INCOME', label: 'Income' },
  { value: 'EXPENSE', label: 'Expense' },
]

interface CategoryRowProps {
  category: Category
  onEdit?: () => void
  onDelete?: () => void
}

function CategoryRow({ category, onEdit, onDelete }: CategoryRowProps) {
  return (
    <li className="flex items-center justify-between gap-3 px-4 py-3">
      <div className="flex min-w-0 items-center gap-3">
        <span className="truncate text-sm font-medium text-slate-900">{category.name}</span>
        <CategoryTypeBadge type={category.type} />
      </div>
      {onEdit && onDelete && (
        <div className="flex shrink-0 gap-1">
          <button
            onClick={onEdit}
            className="rounded-md p-2 text-slate-400 hover:bg-slate-100 hover:text-slate-700"
            aria-label={`Rename ${category.name}`}
          >
            <Pencil size={16} />
          </button>
          <button
            onClick={onDelete}
            className="rounded-md p-2 text-slate-400 hover:bg-rose-50 hover:text-rose-600"
            aria-label={`Delete ${category.name}`}
          >
            <Trash2 size={16} />
          </button>
        </div>
      )}
    </li>
  )
}

function Section({ title, description, children }: { title: string; description: string; children: ReactNode }) {
  return (
    <section className="mb-8">
      <h2 className="text-base font-semibold text-slate-900">{title}</h2>
      <p className="mb-3 text-sm text-slate-500">{description}</p>
      {children}
    </section>
  )
}

function DeleteCategoryDialog({ category, onClose }: { category: Category; onClose: () => void }) {
  const queryClient = useQueryClient()

  const mutation = useMutation({
    mutationFn: () => categoriesApi.remove(category.id),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: CATEGORIES_KEY })
      onClose()
    },
  })

  return (
    <ConfirmDialog
      title="Delete category"
      message={
        <>
          Delete <span className="font-medium text-slate-900">{category.name}</span>? It will no longer be available
          for new transactions. Existing transactions are not deleted.
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

export default function CategoriesPage() {
  const { data, isLoading, error, refetch } = useCategories()
  const [filter, setFilter] = useState<Filter>('ALL')
  const [editing, setEditing] = useState<Category | 'new' | null>(null)
  const [deleting, setDeleting] = useState<Category | null>(null)

  const visible = (data ?? []).filter((category) => filter === 'ALL' || isCategoryCompatible(category, filter))
  const custom = visible.filter((category) => !category.is_default)
  const defaults = visible.filter((category) => category.is_default)

  return (
    <>
      <PageHeader
        title="Categories"
        description="Organize your income and expenses"
        actions={
          <Button onClick={() => setEditing('new')}>
            <Plus size={16} />
            Add category
          </Button>
        }
      />

      <div className="mb-6 inline-flex rounded-lg bg-slate-100 p-1">
        {filters.map(({ value, label }) => (
          <button
            key={value}
            onClick={() => setFilter(value)}
            className={`rounded-md px-4 py-1.5 text-sm font-medium transition ${
              filter === value ? 'bg-white text-slate-900 shadow-sm' : 'text-slate-500 hover:text-slate-700'
            }`}
          >
            {label}
          </button>
        ))}
      </div>

      {isLoading && (
        <div className="space-y-2">
          {[0, 1, 2, 3, 4].map((item) => (
            <div key={item} className="h-12 animate-pulse rounded-lg bg-slate-200" />
          ))}
        </div>
      )}

      {error && (
        <div className="rounded-xl bg-rose-50 p-5 text-sm text-rose-700">
          <p>{error.message}</p>
          <Button variant="secondary" className="mt-3" onClick={() => refetch()}>
            Try again
          </Button>
        </div>
      )}

      {data && (
        <>
          <Section title="Your categories" description="Categories you created. You can rename or delete these.">
            {custom.length === 0 ? (
              <div className="rounded-xl border border-dashed border-slate-300 bg-white p-6 text-center text-sm text-slate-500">
                No custom categories here yet.
              </div>
            ) : (
              <ul className="divide-y divide-slate-100 rounded-xl bg-white shadow-sm ring-1 ring-slate-200">
                {custom.map((category) => (
                  <CategoryRow
                    key={category.id}
                    category={category}
                    onEdit={() => setEditing(category)}
                    onDelete={() => setDeleting(category)}
                  />
                ))}
              </ul>
            )}
          </Section>

          <Section title="Default categories" description="Built in for everyone. These cannot be changed.">
            {defaults.length === 0 ? (
              <div className="rounded-xl border border-dashed border-slate-300 bg-white p-6 text-center text-sm text-slate-500">
                No default categories to show.
              </div>
            ) : (
              <ul className="divide-y divide-slate-100 rounded-xl bg-white shadow-sm ring-1 ring-slate-200">
                {defaults.map((category) => (
                  <CategoryRow key={category.id} category={category} />
                ))}
              </ul>
            )}
          </Section>
        </>
      )}

      {editing && (
        <CategoryFormModal category={editing === 'new' ? null : editing} onClose={() => setEditing(null)} />
      )}
      {deleting && <DeleteCategoryDialog category={deleting} onClose={() => setDeleting(null)} />}
    </>
  )
}