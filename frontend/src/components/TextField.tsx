import type { ComponentProps } from 'react'

interface TextFieldProps extends ComponentProps<'input'> {
  label: string
  error?: string
}

export function TextField({ label, error, id, className = '', ...props }: TextFieldProps) {
  const inputId = id ?? props.name

  return (
    <div>
      <label htmlFor={inputId} className="mb-1.5 block text-sm font-semibold text-slate-700">
        {label}
      </label>
      <input
        id={inputId}
        aria-invalid={Boolean(error)}
        className={`w-full rounded-xl border bg-glass/[0.04] px-3.5 py-2.5 text-sm text-slate-900 outline-none transition focus:border-emerald-500/60 focus:ring-4 focus:ring-emerald-500/15 ${
          error ? 'border-rose-400' : 'border-glass/10'
        } ${className}`}
        {...props}
      />
      {error && <p className="mt-1 text-xs text-rose-600">{error}</p>}
    </div>
  )
}