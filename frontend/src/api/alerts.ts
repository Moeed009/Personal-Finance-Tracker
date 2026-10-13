import { api } from '@/api/client'
import type { Alert } from '@/types/api'

export const alertsApi = {
  list: () => api.get<Alert[]>('/alerts'),
  markRead: (id: string) => api.patch<Alert>(`/alerts/${id}/read`),
  markAllRead: () => api.post<{ updated: number }>('/alerts/read-all'),
}
