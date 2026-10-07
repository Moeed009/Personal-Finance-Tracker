import { api } from '@/api/client'
import { monthStart } from '@/lib/months'
import type { MonthlyReport } from '@/types/api'

export const reportsApi = {
  monthly: (month: string) => api.get<MonthlyReport>('/reports/monthly', { month: monthStart(month) }),
}