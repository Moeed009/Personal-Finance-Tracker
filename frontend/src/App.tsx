import { lazy, Suspense, type ReactNode } from 'react'
import { BrowserRouter, Navigate, Route, Routes, useLocation } from 'react-router-dom'
import { QueryClientProvider } from '@tanstack/react-query'
import { queryClient } from '@/lib/queryClient'
import { AuthProvider } from '@/components/AuthProvider'
import { AppLayout } from '@/components/AppLayout'
import { ProtectedRoute, PublicOnlyRoute } from '@/components/ProtectedRoute'
import { PageLoader } from '@/components/PageLoader'

// Each page is its own chunk, so the first visit downloads only what it shows.
const LoginPage = lazy(() => import('@/pages/LoginPage'))
const RegisterPage = lazy(() => import('@/pages/RegisterPage'))
const ForgotPasswordPage = lazy(() => import('@/pages/ForgotPasswordPage'))
const ResetPasswordPage = lazy(() => import('@/pages/ResetPasswordPage'))
const DashboardPage = lazy(() => import('@/pages/DashboardPage'))
const TransactionsPage = lazy(() => import('@/pages/TransactionsPage'))
const ImportsPage = lazy(() => import('@/pages/ImportsPage'))
const AccountsPage = lazy(() => import('@/pages/AccountsPage'))
const CategoriesPage = lazy(() => import('@/pages/CategoriesPage'))
const BudgetsPage = lazy(() => import('@/pages/BudgetsPage'))
const GoalsPage = lazy(() => import('@/pages/GoalsPage'))
const RecurringPage = lazy(() => import('@/pages/RecurringPage'))
const ReportsPage = lazy(() => import('@/pages/ReportsPage'))
const AlertsPage = lazy(() => import('@/pages/AlertsPage'))
const SettingsPage = lazy(() => import('@/pages/SettingsPage'))

function RecoveryLinkGate({ children }: { children: ReactNode }) {
  const { pathname, search, hash } = useLocation()
  const query = new URLSearchParams(search)
  const fragment = new URLSearchParams(hash.replace(/^#/, ''))

  const isRecoveryLink =
    (query.get('type') === 'recovery' && query.has('token_hash')) ||
    (fragment.get('type') === 'recovery' && fragment.has('access_token'))

  if (isRecoveryLink && pathname !== '/reset-password') {
    return <Navigate to={{ pathname: '/reset-password', search, hash }} replace />
  }

  return <>{children}</>
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <AuthProvider>
          <RecoveryLinkGate>
            <Suspense fallback={<PageLoader fullScreen />}>
            <Routes>
              <Route path="/reset-password" element={<ResetPasswordPage />} />

              <Route element={<PublicOnlyRoute />}>
                <Route path="/login" element={<LoginPage />} />
                <Route path="/register" element={<RegisterPage />} />
                <Route path="/forgot-password" element={<ForgotPasswordPage />} />
              </Route>

              <Route element={<ProtectedRoute />}>
                <Route element={<AppLayout />}>
                  <Route path="/" element={<DashboardPage />} />
                  <Route path="/transactions" element={<TransactionsPage />} />
                  <Route path="/imports" element={<ImportsPage />} />
                  <Route path="/accounts" element={<AccountsPage />} />
                  <Route path="/categories" element={<CategoriesPage />} />
                  <Route path="/budgets" element={<BudgetsPage />} />
                  <Route path="/goals" element={<GoalsPage />} />
                  <Route path="/recurring" element={<RecurringPage />} />
                  <Route path="/reports" element={<ReportsPage />} />
                  <Route path="/alerts" element={<AlertsPage />} />
                  <Route path="/settings" element={<SettingsPage />} />
                </Route>
              </Route>

              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
            </Suspense>
          </RecoveryLinkGate>
        </AuthProvider>
      </BrowserRouter>
    </QueryClientProvider>
  )
}