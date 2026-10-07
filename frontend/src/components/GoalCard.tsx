import { CheckCircle2, Pencil, Plus, Trash2 } from 'lucide-react'
import { Button } from '@/components/Button'
import { daysUntil } from '@/lib/dates'
import { formatDay, formatMoney } from '@/lib/format'
import type { Goal } from '@/types/api'

interface GoalCardProps {
  goal: Goal
  currency: string
  onContribute: () => void
  onEdit: () => void
  onDelete: () => void
}

function timeLeft(targetDate: string): { label: string; overdue: boolean } {
  const days = daysUntil(targetDate)
  if (days < 0) return { label: 'Target date passed', overdue: true }
  if (days === 0) return { label: 'Due today', overdue: false }
  if (days <= 30) return { label: `${days} day${days === 1 ? '' : 's'} left`, overdue: false }
  return { label: `about ${Math.ceil(days / 30)} months left`, overdue: false }
}

export function GoalCard({ goal, currency, onContribute, onEdit, onDelete }: GoalCardProps) {
  const isCompleted = goal.status === 'COMPLETED'
  const percent = Number(goal.progress_percent)
  const remaining = timeLeft(goal.target_date)

  return (
    <div className="rounded-xl bg-white p-5 shadow-sm ring-1 ring-slate-200">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <p className="truncate font-medium text-slate-900">{goal.name}</p>
          {isCompleted ? (
            <span className="mt-1 inline-flex items-center gap-1 rounded-full bg-emerald-50 px-2.5 py-0.5 text-xs font-medium text-emerald-700">
              <CheckCircle2 size={12} />
              Completed
            </span>
          ) : (
            <p className={`mt-1 text-xs ${remaining.overdue ? 'font-medium text-rose-600' : 'text-slate-500'}`}>
              {formatDay(goal.target_date)} · {remaining.label}
            </p>
          )}
        </div>
        <div className="flex shrink-0 gap-1">
          <button
            onClick={onEdit}
            className="rounded-md p-2 text-slate-400 hover:bg-slate-100 hover:text-slate-700"
            aria-label={`Edit ${goal.name}`}
          >
            <Pencil size={16} />
          </button>
          <button
            onClick={onDelete}
            className="rounded-md p-2 text-slate-400 hover:bg-rose-50 hover:text-rose-600"
            aria-label={`Delete ${goal.name}`}
          >
            <Trash2 size={16} />
          </button>
        </div>
      </div>

      <div className="mt-4 h-2 overflow-hidden rounded-full bg-slate-100">
        <div
          className={`h-full rounded-full ${isCompleted ? 'bg-emerald-500' : 'bg-indigo-500'}`}
          style={{ width: `${Math.min(100, percent)}%` }}
        />
      </div>

      <div className="mt-3 flex items-baseline justify-between text-sm">
        <span className="text-slate-900">
          <span className="font-semibold">{formatMoney(goal.saved_amount, currency)}</span>
          <span className="text-slate-500"> of {formatMoney(goal.target_amount, currency)}</span>
        </span>
        <span className="font-medium text-slate-600">{percent.toFixed(0)}%</span>
      </div>

      {!isCompleted && Number(goal.required_monthly_saving) > 0 && (
        <p className="mt-1 text-xs text-slate-500">
          Save {formatMoney(goal.required_monthly_saving, currency)} per month to reach it on time.
        </p>
      )}

      {!isCompleted && (
        <Button className="mt-4" variant="secondary" onClick={onContribute}>
          <Plus size={16} />
          Add savings
        </Button>
      )}
    </div>
  )
}