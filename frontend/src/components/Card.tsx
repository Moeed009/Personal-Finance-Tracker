import type { ReactNode } from 'react'
import { Button } from '@/components/Button'

interface CardProps {
  title: string
  subtitle?: string
  action?: ReactNode
  isLoading?: boolean
  error?: Error | null
  onRetry?: () => void
  children: ReactNode
}

export function Card({ title, subtitle, action, isLoading = false, error, onRetry, children }: CardProps) {
  return (
    <section className="rounded-xl bg-white p-5 shadow-sm ring-1 ring-slate-200">
      <div className="mb-4 flex items-start justify-between gap-3">
        <div>
          <h2 className="text-base font-semibold text-slate-900">{title}</h2>
          {subtitle && <p className="text-xs text-slate-500">{subtitle}</p>}
        </div>
        {action}
      </div>

      {isLoading ? (
        <div className="h-40 animate-pulse rounded-lg bg-slate-100" />
      ) : error ? (
        <div className="rounded-lg bg-rose-50 p-4 text-sm text-rose-700">
          <p>{error.message}</p>
          {onRetry && (
            <Button variant="secondary" className="mt-3" onClick={onRetry}>
              Try again
            </Button>
          )}
        </div>
      ) : (
        children
      )}
    </section>
  )
}