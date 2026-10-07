import { useState } from 'react'
import { Link } from 'react-router-dom'
import { AlertTriangle, Bell, CalendarClock, TrendingUp, XCircle, type LucideIcon } from 'lucide-react'
import { Button } from '@/components/Button'
import { PageHeader } from '@/components/PageHeader'
import { useAlerts } from '@/hooks/useAlerts'
import { formatDateTime } from '@/lib/format'
import type { AlertType } from '@/types/api'

type Group = 'BUDGET' | 'UNUSUAL' | 'RECURRING'
type Filter = 'ALL' | Group

const filters: { value: Filter; label: string }[] = [
  { value: 'ALL', label: 'All' },
  { value: 'BUDGET', label: 'Budgets' },
  { value: 'UNUSUAL', label: 'Unusual' },
  { value: 'RECURRING', label: 'Recurring' },
]

interface AlertStyle {
  label: string
  group: Group
  icon: LucideIcon
  iconClass: string
  bgClass: string
  to: string
}

const alertStyles: Record<AlertType, AlertStyle> = {
  BUDGET_WARNING: {
    label: 'Budget warning',
    group: 'BUDGET',
    icon: AlertTriangle,
    iconClass: 'text-amber-600',
    bgClass: 'bg-amber-50',
    to: '/budgets',
  },
  BUDGET_EXCEEDED: {
    label: 'Budget exceeded',
    group: 'BUDGET',
    icon: XCircle,
    iconClass: 'text-rose-600',
    bgClass: 'bg-rose-50',
    to: '/budgets',
  },
  UNUSUAL_SPENDING: {
    label: 'Unusual spending',
    group: 'UNUSUAL',
    icon: TrendingUp,
    iconClass: 'text-violet-600',
    bgClass: 'bg-violet-50',
    to: '/transactions',
  },
  RECURRING_DUE: {
    label: 'Payment due soon',
    group: 'RECURRING',
    icon: CalendarClock,
    iconClass: 'text-sky-600',
    bgClass: 'bg-sky-50',
    to: '/recurring',
  },
}

export default function AlertsPage() {
  const { data, isLoading, error, refetch } = useAlerts()
  const [filter, setFilter] = useState<Filter>('ALL')

  const visible = (data ?? []).filter((alert) => filter === 'ALL' || alertStyles[alert.alert_type].group === filter)

  return (
    <>
      <PageHeader title="Alerts" description="Budget limits, unusual spending and upcoming payments" />

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
          {[0, 1, 2, 3].map((item) => (
            <div key={item} className="h-16 animate-pulse rounded-lg bg-slate-200" />
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

      {data && visible.length === 0 && (
        <div className="rounded-xl border border-dashed border-slate-300 bg-white p-10 text-center">
          <Bell className="mx-auto text-slate-400" size={32} />
          <p className="mt-3 font-medium text-slate-900">{filter === 'ALL' ? 'No alerts yet' : 'No alerts in this group'}</p>
          <p className="mt-1 text-sm text-slate-500">
            You will see an alert when a budget nears its limit, spending looks unusual or a recurring payment is due.
          </p>
        </div>
      )}

      {data && visible.length > 0 && (
        <ul className="divide-y divide-slate-100 rounded-xl bg-white shadow-sm ring-1 ring-slate-200">
          {visible.map((alert) => {
            const style = alertStyles[alert.alert_type]
            const Icon = style.icon

            return (
              <li key={alert.id} className="flex gap-3 px-4 py-4">
                <span className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-lg ${style.bgClass}`}>
                  <Icon size={18} className={style.iconClass} />
                </span>
                <div className="min-w-0 flex-1">
                  <div className="flex flex-wrap items-center gap-x-2">
                    <span className="text-sm font-medium text-slate-900">{style.label}</span>
                    <span className="text-xs text-slate-500">{formatDateTime(alert.created_at)}</span>
                  </div>
                  <p className="mt-0.5 text-sm text-slate-600">{alert.message}</p>
                </div>
                <Link to={style.to} className="shrink-0 self-center text-sm font-medium text-indigo-600 hover:underline">
                  View
                </Link>
              </li>
            )
          })}
        </ul>
      )}
    </>
  )
}