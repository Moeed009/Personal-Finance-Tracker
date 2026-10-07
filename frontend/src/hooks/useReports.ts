import { useQuery } from '@tanstack/react-query'
import { reportsApi } from '@/api/reports'

export const REPORTS_KEY = ['reports'] as const

export function useMonthlyReport(month: string) {
  return useQuery({
    queryKey: [...REPORTS_KEY, month],
    queryFn: () => reportsApi.monthly(month),
  })
}