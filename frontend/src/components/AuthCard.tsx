import type { ReactNode } from 'react'
import { Check, ShieldCheck } from 'lucide-react'
import { Logo } from '@/components/Logo'

interface AuthCardProps {
  title: string
  subtitle: string
  children: ReactNode
  footer: ReactNode
}

function BrandPanel() {
  return (
    <section
      aria-label="About Finance Tracker"
      className="relative hidden flex-1 flex-col justify-between gap-12 overflow-hidden p-12 lg:flex xl:p-16"
      style={{
        background:
          'radial-gradient(700px 500px at 20% 10%, rgba(16,185,129,0.35), transparent 60%), radial-gradient(600px 400px at 90% 90%, rgba(233,185,73,0.22), transparent 60%), linear-gradient(160deg, #0b3b2d, #07140f 70%)',
      }}
    >
      <div
        aria-hidden="true"
        className="absolute inset-0"
        style={{
          backgroundImage:
            'linear-gradient(rgba(255,255,255,0.035) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.035) 1px, transparent 1px)',
          backgroundSize: '48px 48px',
        }}
      />

      <div className="relative">
        <Logo size={44} />
      </div>

      <div aria-hidden="true" className="relative h-72 max-w-lg">
        <div className="animate-float absolute left-0 top-2 w-72 rounded-3xl border border-emerald-500/30 bg-gradient-to-br from-emerald-500/50 to-[#06281e]/90 p-6 shadow-2xl backdrop-blur">
          <p className="text-xs font-semibold uppercase tracking-widest text-emerald-800">Total balance</p>
          <p className="mt-2 font-display text-3xl font-bold">PKR 12,581</p>
          <svg viewBox="0 0 260 48" className="mt-3 h-12 w-full">
            <path
              d="M0 40 C 30 36, 50 42, 80 30 S 130 34, 160 24 S 210 26, 260 6"
              fill="none"
              stroke="#f5d68a"
              strokeWidth="2.5"
              strokeLinecap="round"
            />
          </svg>
        </div>

        <div
          className="animate-float absolute right-0 top-0 w-48 rounded-3xl border border-glass/10 bg-[#0a1612]/80 p-5 shadow-2xl backdrop-blur"
          style={{ animationDelay: '0.8s' }}
        >
          <p className="text-xs text-slate-500">Budget used</p>
          <div
            className="mt-3 flex h-20 w-20 items-center justify-center rounded-full"
            style={{ background: 'conic-gradient(#e9b949 0 72%, rgba(255,255,255,0.08) 72% 100%)' }}
          >
            <div className="flex h-15 w-15 items-center justify-center rounded-full bg-[#0b1411] font-display text-lg font-bold">
              72%
            </div>
          </div>
        </div>

        <div
          className="animate-float absolute bottom-0 right-10 flex w-64 items-center gap-3 rounded-2xl border border-glass/10 bg-[#0a1612]/85 p-4 shadow-2xl"
          style={{ animationDelay: '1.6s' }}
        >
          <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-emerald-500/20 text-emerald-600">
            <Check size={20} />
          </span>
          <div>
            <p className="text-sm font-bold">Statement imported</p>
            <p className="text-xs text-slate-500">CSV or PDF, any bank</p>
          </div>
        </div>
      </div>

      <div className="relative max-w-lg space-y-5">
        <h2 className="text-4xl font-bold leading-tight tracking-tight xl:text-5xl">
          Every rupee, <span className="text-gradient-gold">finally clear.</span>
        </h2>
        <p className="text-base leading-relaxed text-slate-600">
          Import statements from your bank or wallet, set budgets that warn you in time, and see exactly where your
          money goes each month.
        </p>
        <ul className="flex flex-wrap gap-2.5 text-sm font-semibold">
          {['CSV and PDF import', 'Smart budgets', 'Recurring payments'].map((feature) => (
            <li key={feature} className="rounded-full border border-glass/10 bg-glass/5 px-3.5 py-2">
              {feature}
            </li>
          ))}
        </ul>
      </div>
    </section>
  )
}

export function AuthCard({ title, subtitle, children, footer }: AuthCardProps) {
  return (
    <div className="flex min-h-dvh bg-[#060b09]">
      <BrandPanel />

      <main
        className="flex flex-1 items-center justify-center px-5 py-10 sm:px-10"
        style={{ background: 'radial-gradient(600px 400px at 50% 0%, rgba(16,185,129,0.10), transparent 70%), #070d0b' }}
      >
        <div className="animate-rise w-full max-w-md">
          <div className="mb-10 lg:hidden">
            <Logo size={40} />
          </div>

          <h1 className="text-3xl font-bold tracking-tight text-slate-900">{title}</h1>
          <p className="mt-2 text-sm text-slate-500">{subtitle}</p>

          <div className="mt-8">{children}</div>

          <p className="mt-8 text-center text-sm text-slate-500">{footer}</p>

          <p className="mt-6 flex items-center justify-center gap-2 text-xs text-slate-500">
            <ShieldCheck size={14} />
            Your data is private to your account.
          </p>
        </div>
      </main>
    </div>
  )
}
