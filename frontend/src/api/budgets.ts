import { api } from '@/api/client'
import { monthStart } from '@/lib/months'
import type { Budget, BudgetInput } from '@/types/api'

export const budgetsApi = {
  list: (month: string) => api.get<Budget[]>('/budgets', { month: monthStart(month) }),
  create: (input: BudgetInput) => api.post<Budget>('/budgets', input),
  update: (id: string, limitAmount: string) => api.patch<Budget>(`/budgets/${id}`, { limit_amount: limitAmount }),
  remove: (id: string) => api.delete(`/budgets/${id}`),
}