export function PageLoader({ fullScreen = false }: { fullScreen?: boolean }) {
  return (
    <div
      role="status"
      aria-label="Loading"
      className={`flex items-center justify-center ${fullScreen ? 'min-h-dvh' : 'min-h-[50vh]'}`}
    >
      <span className="h-9 w-9 animate-spin rounded-full border-2 border-emerald-500/25 border-t-emerald-500" />
    </div>
  )
}
