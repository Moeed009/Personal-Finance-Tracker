import { useMutation, useQueryClient } from '@tanstack/react-query'
import { Repeat } from 'lucide-react'
import { recurringApi } from '@/api/recurring'
import { Button } from '@/components/Button'
import { formatMoney } from '@/lib/format'
import { invalidateFinanceData } from '@/lib/invalidate'
import { dueInfo, FREQUENCY_LABELS, type DueTone } from '@/lib/recurring'
import type { RecurringExpense, RecurringStatus } from '@/types/api'

interface RecurringCardProps {
  item: RecurringExpense
  accountName: string
  categoryName: string
  currency: string
}

const statusBadges: Record<RecurringStatus, { label: string; className: string }> = {
  DETECTED: { label: 'Needs review', className: 'bg-amber-50 text-amber-700' },
  CONFIRMED: { label: 'Confirmed', className: 'bg-emerald-50 text-emerald-700' },
  DISMISSED: { label: 'Dismissed', className: 'bg-slate-100 text-slate-600' },
}

const dueTones: Record<DueTone, string> = {
  overdue: 'text-rose-600',
  soon: 'text-amber-600',
  normal: 'text-slate-500',
}

export function RecurringCard({ item, accountName, categoryName, currency }: RecurringCardProps) {
  const queryClient = useQueryClient()

  const mutation = useMutation({
    mutationFn: (status: 'CONFIRMED' | 'DISMISSED') => recurringApi.setStatus(item.id, status),
    onSuccess: () => invalidateFinanceData(queryClient),
  })

  const badge = statusBadges[item.status]
  const due = dueInfo(item.next_due_date)
  const isDismissed = item.status === 'DISMISSED'

  return (
    <div className={`rounded-xl bg-white p-5 shadow-sm ring-1 ring-slate-200 ${isDismissed ? 'opacity-75' : ''}`}>
      <div className="flex items-start justify-between gap-3">
        <div className="flex min-w-0 items-center gap-3">
          <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-indigo-50 text-indigo-600">
            <Repeat size={18} />
          </span>
          <div className="min-w-0">
            <p className="truncate font-medium capitalize text-slate-900">{item.merchant}</p>
            <p className="truncate text-xs text-slate-500">
              {categoryName} · {accountName}
            </p>
          </div>
        </div>
        <span className={`shrink-0 rounded-full px-2.5 py-0.5 text-xs font-medium ${badge.className}`}>
          {badge.label}
        </span>
      </div>

      <div className="mt-4 flex items-baseline justify-between">
        <p className="text-xl font-semibold text-slate-900">{formatMoney(item.avg_amount, currency)}</p>
        <p className="text-sm text-slate-500">{FREQUENCY_LABELS[item.frequency]}</p>
      </div>

      {!isDismissed && <p className={`mt-1 text-sm font-medium ${dueTones[due.tone]}`}>{due.label}</p>}

      {mutation.error && <p className="mt-3 text-sm text-rose-600">{mutation.error.message}</p>}

      <div className="mt-4 flex gap-2">
        {item.status === 'DETECTED' && (
          <Button disabled={mutation.isPending} onClick={() => mutation.mutate('CONFIRMED')}>
            Confirm
          </Button>
        )}
        {item.status === 'DISMISSED' ? (
          <Button variant="secondary" disabled={mutation.isPending} onClick={() => mutation.mutate('CONFIRMED')}>
            Restore
          </Button>
        ) : (
          <Button variant="secondary" disabled={mutation.isPending} onClick={() => mutation.mutate('DISMISSED')}>
            Dismiss
          </Button>
        )}
      </div>
    </div>
  )
}