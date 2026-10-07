import { api } from '@/api/client'
import type { Goal, GoalInput, GoalPatch } from '@/types/api'

export const goalsApi = {
  list: () => api.get<Goal[]>('/goals'),
  create: (input: GoalInput) => api.post<Goal>('/goals', input),
  update: (id: string, patch: GoalPatch) => api.put<Goal>(`/goals/${id}`, patch),
  remove: (id: string) => api.delete(`/goals/${id}`),
  contribute: (id: string, amount: string) => api.post<Goal>(`/goals/${id}/contribute`, { amount }),
}