import { X } from 'lucide-react'
import type { ImportSummary } from '@/types/api'

interface ImportSummaryCardProps {
  summary: ImportSummary
  onDismiss: () => void
}

function Stat({ label, value, className }: { label: string; value: number; className: string }) {
  return (
    <div className="rounded-lg bg-slate-50 p-3">
      <p className="text-xs text-slate-500">{label}</p>
      <p className={`text-xl font-semibold ${className}`}>{value}</p>
    </div>
  )
}

export function ImportSummaryCard({ summary, onDismiss }: ImportSummaryCardProps) {
  const allDuplicates = summary.rows_imported === 0 && summary.rows_skipped > 0 && summary.rows_failed === 0

  return (
    <div className="mt-6 rounded-xl bg-white p-6 shadow-sm ring-1 ring-slate-200">
      <div className="flex items-start justify-between gap-3">
        <div>
          <h2 className="text-base font-semibold text-slate-900">Import finished</h2>
          <p className="mt-1 text-sm text-slate-500">{summary.filename}</p>
        </div>
        <button
          onClick={onDismiss}
          className="rounded-md p-1 text-slate-400 hover:bg-slate-100 hover:text-slate-600"
          aria-label="Dismiss"
        >
          <X size={18} />
        </button>
      </div>

      {allDuplicates && (
        <p className="mt-3 rounded-lg bg-amber-50 px-3 py-2 text-sm text-amber-800">
          All rows were already imported before, so nothing new was added.
        </p>
      )}

      <div className="mt-4 grid grid-cols-2 gap-3 sm:grid-cols-4">
        <Stat label="Total rows" value={summary.rows_total} className="text-slate-900" />
        <Stat label="Imported" value={summary.rows_imported} className="text-emerald-600" />
        <Stat label="Skipped (duplicates)" value={summary.rows_skipped} className="text-amber-600" />
        <Stat label="Failed" value={summary.rows_failed} className="text-rose-600" />
      </div>

      {summary.errors.length > 0 && (
        <div className="mt-4">
          <p className="mb-2 text-sm font-medium text-slate-700">Rows that could not be imported</p>
          <ul className="max-h-48 divide-y divide-slate-100 overflow-y-auto rounded-lg ring-1 ring-slate-200">
            {summary.errors.map((error) => (
              <li key={`${error.row}-${error.message}`} className="flex gap-3 px-3 py-2 text-sm">
                <span className="w-16 shrink-0 text-slate-500">Line {error.row}</span>
                <span className="text-rose-700">{error.message}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}