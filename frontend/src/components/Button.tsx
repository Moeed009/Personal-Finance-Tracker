import type { ComponentProps } from 'react'

type Variant = 'primary' | 'secondary' | 'danger' | 'gold'

interface ButtonProps extends ComponentProps<'button'> {
  variant?: Variant
}

const variants: Record<Variant, string> = {
  primary:
    'bg-gradient-to-br from-[#34d399] via-[#10b981] to-[#0e9f6e] text-[#04140e] font-bold hover:-translate-y-px hover:shadow-[0_12px_30px_-12px_rgba(16,185,129,0.8)]',
  secondary: 'bg-glass/5 text-slate-700 ring-1 ring-glass/10 hover:bg-glass/10 hover:text-slate-900',
  danger:
    'bg-gradient-to-br from-[#fb7185] to-[#e11d48] text-[#1a0509] font-bold hover:-translate-y-px hover:shadow-[0_12px_30px_-12px_rgba(244,63,94,0.7)]',
  gold: 'bg-gradient-to-br from-[#f5d68a] to-[#e9b949] text-[#1a1405] font-bold hover:-translate-y-px hover:shadow-[0_10px_28px_-8px_rgba(233,185,73,0.6)]',
}

export function Button({ variant = 'primary', type = 'button', className = '', ...props }: ButtonProps) {
  return (
    <button
      type={type}
      className={`inline-flex items-center justify-center gap-2 rounded-xl px-4 py-2.5 text-sm font-semibold transition-all duration-200 disabled:cursor-not-allowed disabled:opacity-60 disabled:hover:translate-y-0 ${variants[variant]} ${className}`}
      {...props}
    />
  )
}
