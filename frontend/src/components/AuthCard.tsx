import type { ReactNode } from 'react'

interface AuthCardProps {
  title: string
  subtitle: string
  children: ReactNode
  footer: ReactNode
}


const BACKGROUND_IMAGE = '/login-bg.svg'

export function AuthCard({ title, subtitle, children, footer }: AuthCardProps) {
  return (
    <main
      className="flex min-h-screen items-center justify-center bg-slate-900 bg-cover bg-center px-4 py-10"
      style={{ backgroundImage: `url(${BACKGROUND_IMAGE})` }}
    >
      <div className="w-full max-w-md rounded-2xl bg-white p-8 shadow-2xl ring-1 ring-white/20">
        <h1 className="text-2xl font-semibold text-slate-900">{title}</h1>
        <p className="mt-1 text-sm text-slate-500">{subtitle}</p>
        <div className="mt-6">{children}</div>
        <p className="mt-6 text-center text-sm text-slate-500">{footer}</p>
      </div>
    </main>
  )
}
