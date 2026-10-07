import { ChevronLeft, ChevronRight } from 'lucide-react'
import { currentMonth, monthLabel, shiftMonth } from '@/lib/months'

interface MonthSwitcherProps {
  month: string
  onChange: (month: string) => void
}

export function MonthSwitcher({ month, onChange }: MonthSwitcherProps) {
  const isCurrent = month === currentMonth()

  return (
    <div className="mb-6 flex flex-wrap items-center gap-3">
      <div className="inline-flex items-center gap-1 rounded-lg bg-white p-1 shadow-sm ring-1 ring-slate-200">
        <button
          onClick={() => onChange(shiftMonth(month, -1))}
          className="rounded-md p-2 text-slate-500 hover:bg-slate-100"
          aria-label="Previous month"
        >
          <ChevronLeft size={16} />
        </button>
        <span className="min-w-36 px-2 text-center text-sm font-medium text-slate-900">{monthLabel(month)}</span>
        <button
          onClick={() => onChange(shiftMonth(month, 1))}
          className="rounded-md p-2 text-slate-500 hover:bg-slate-100"
          aria-label="Next month"
        >
          <ChevronRight size={16} />
        </button>
      </div>
      {!isCurrent && (
        <button
          onClick={() => onChange(currentMonth())}
          className="text-sm font-medium text-indigo-600 hover:underline"
        >
          Back to this month
        </button>
      )}
    </div>
  )
}