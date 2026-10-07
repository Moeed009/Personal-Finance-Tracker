import { daysUntil } from '@/lib/dates'
import { formatDay } from '@/lib/format'
import type { RecurringFrequency } from '@/types/api'

export const FREQUENCY_LABELS: Record<RecurringFrequency, string> = {
  WEEKLY: 'Weekly',
  BIWEEKLY: 'Every 2 weeks',
  MONTHLY: 'Monthly',
}

export type DueTone = 'overdue' | 'soon' | 'normal'

export function dueInfo(nextDueDate: string): { label: string; tone: DueTone } {
  const days = daysUntil(nextDueDate)

  if (days < 0) return { label: `Overdue by ${-days} day${days === -1 ? '' : 's'}`, tone: 'overdue' }
  if (days === 0) return { label: 'Due today', tone: 'soon' }
  if (days <= 3) return { label: `Due in ${days} day${days === 1 ? '' : 's'}`, tone: 'soon' }
  return { label: `Next: ${formatDay(nextDueDate)}`, tone: 'normal' }
}