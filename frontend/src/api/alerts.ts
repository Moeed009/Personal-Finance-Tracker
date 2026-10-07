import { api } from '@/api/client'
import type { Alert } from '@/types/api'

export const alertsApi = {
  list: () => api.get<Alert[]>('/alerts'),
}