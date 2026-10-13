interface LogoProps {
  size?: number
  showName?: boolean
  subtitle?: string
}

export function Logo({ size = 36, showName = true, subtitle }: LogoProps) {
  return (
    <div className="flex items-center gap-3">
      <svg width={size} height={size} viewBox="0 0 48 48" fill="none" aria-hidden="true" className="shrink-0">
        <rect width="48" height="48" rx="12" fill="#104234" />
        <rect x="11" y="27" width="6" height="10" rx="2" fill="#4ab88f" />
        <rect x="21" y="20" width="6" height="17" rx="2" fill="#80d2b1" />
        <rect x="31" y="11" width="6" height="26" rx="2" fill="#e9b949" />
      </svg>
      {showName && (
        <span className="flex flex-col leading-tight">
          <span className="font-display text-base font-bold tracking-tight text-slate-900">Finance Tracker</span>
          {subtitle && <span className="text-xs text-slate-500">{subtitle}</span>}
        </span>
      )}
    </div>
  )
}
