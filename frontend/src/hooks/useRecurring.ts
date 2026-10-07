import { useQuery } from '@tanstack/react-query'
import { recurringApi } from '@/api/recurring'

export const RECURRING_KEY = ['recurring'] as const

export function useRecurring() {
  return useQuery({
    queryKey: RECURRING_KEY,
    queryFn: recurringApi.list,
  })
}