import { CATEGORY_TYPE_LABELS } from '@/lib/constants'
import type { CategoryType } from '@/types/api'

const styles: Record<CategoryType, string> = {
  INCOME: 'bg-emerald-50 text-emerald-700',
  EXPENSE: 'bg-rose-50 text-rose-700',
  BOTH: 'bg-slate-100 text-slate-600',
}

export function CategoryTypeBadge({ type }: { type: CategoryType }) {
  return (
    <span className={`rounded-full px-2.5 py-0.5 text-xs font-medium ${styles[type]}`}>
      {CATEGORY_TYPE_LABELS[type]}
    </span>
  )
}