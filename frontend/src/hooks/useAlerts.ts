import { useQuery } from '@tanstack/react-query'
import { alertsApi } from '@/api/alerts'

export const ALERTS_KEY = ['alerts'] as const

export function useAlerts() {
  return useQuery({
    queryKey: ALERTS_KEY,
    queryFn: alertsApi.list,
  })
}