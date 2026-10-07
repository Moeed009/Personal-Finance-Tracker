import { api } from '@/api/client'
import type { DetectionResult, RecurringExpense, RecurringList } from '@/types/api'

export const recurringApi = {
  list: () => api.get<RecurringList>('/recurring'),
  detect: () => api.post<DetectionResult>('/recurring/detect'),
  setStatus: (id: string, status: 'CONFIRMED' | 'DISMISSED') =>
    api.patch<RecurringExpense>(`/recurring/${id}`, { status }),
}