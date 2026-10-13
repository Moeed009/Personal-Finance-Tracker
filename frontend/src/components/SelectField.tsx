import type { ComponentProps } from 'react'

interface SelectFieldProps extends ComponentProps<'select'> {
  label: string
  error?: string
}

export function SelectField({ label, error, id, className = '', children, ...props }: SelectFieldProps) {
  const selectId = id ?? props.name

  return (
    <div>
      <label htmlFor={selectId} className="mb-1.5 block text-sm font-semibold text-slate-700">
        {label}
      </label>
      <select
        id={selectId}
        aria-invalid={Boolean(error)}
        className={`w-full rounded-xl border bg-[#101a16] px-3.5 py-2.5 text-sm text-slate-900 outline-none transition focus:border-emerald-500/60 focus:ring-4 focus:ring-emerald-500/15 ${
          error ? 'border-rose-400' : 'border-glass/10'
        } ${className}`}
        {...props}
      >
        {children}
      </select>
      {error && <p className="mt-1 text-xs text-rose-600">{error}</p>}
    </div>
  )
}