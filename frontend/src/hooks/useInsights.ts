import { useQuery } from '@tanstack/react-query'
import { insightsApi } from '@/api/insights'

export const INSIGHTS_KEY = ['insights'] as const
export const TREND_MONTHS = 6

export function useMonthSummary(month: string) {
  return useQuery({
    queryKey: [...INSIGHTS_KEY, 'summary', month],
    queryFn: () => insightsApi.summary(month),
  })
}

export function useCategorySpend(month: string) {
  return useQuery({
    queryKey: [...INSIGHTS_KEY, 'categories', month],
    queryFn: () => insightsApi.categories(month),
  })
}

export function useTrends() {
  return useQuery({
    queryKey: [...INSIGHTS_KEY, 'trends', TREND_MONTHS],
    queryFn: () => insightsApi.trends(TREND_MONTHS),
  })
}

export function useUnusualSpending(month: string) {
  return useQuery({
    queryKey: [...INSIGHTS_KEY, 'unusual', month],
    queryFn: () => insightsApi.unusual(month),
  })
}