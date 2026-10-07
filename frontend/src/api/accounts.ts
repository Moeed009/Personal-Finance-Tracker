import { api } from '@/api/client'
import type { Account, AccountInput, AccountSummary } from '@/types/api'

export const accountsApi = {
  summary: () => api.get<AccountSummary>('/accounts/summary'),
  create: (input: AccountInput) => api.post<Account>('/accounts', input),
  update: (id: string, input: Partial<AccountInput>) => api.patch<Account>(`/accounts/${id}`, input),
  remove: (id: string, force = false) => api.delete(`/accounts/${id}`, force ? { force: true } : undefined),
}