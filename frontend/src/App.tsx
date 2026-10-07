import type { ReactNode } from 'react'
import { BrowserRouter, Navigate, Route, Routes, useLocation } from 'react-router-dom'
import { QueryClientProvider } from '@tanstack/react-query'
import { queryClient } from '@/lib/queryClient'
import { AuthProvider } from '@/components/AuthProvider'
import { AppLayout } from '@/components/AppLayout'
import { ProtectedRoute, PublicOnlyRoute } from '@/components/ProtectedRoute'
import LoginPage from '@/pages/LoginPage'
import RegisterPage from '@/pages/RegisterPage'
import ForgotPasswordPage from '@/pages/ForgotPasswordPage'
import ResetPasswordPage from '@/pages/ResetPasswordPage'
import DashboardPage from '@/pages/DashboardPage'
import TransactionsPage from '@/pages/TransactionsPage'
import ImportsPage from '@/pages/ImportsPage'
import AccountsPage from '@/pages/AccountsPage'
import CategoriesPage from '@/pages/CategoriesPage'
import BudgetsPage from '@/pages/BudgetsPage'
import GoalsPage from '@/pages/GoalsPage'
import RecurringPage from '@/pages/RecurringPage'
import ReportsPage from '@/pages/ReportsPage'
import AlertsPage from '@/pages/AlertsPage'
import SettingsPage from '@/pages/SettingsPage'

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
          </RecoveryLinkGate>
        </AuthProvider>
      </BrowserRouter>
    </QueryClientProvider>
  )
}