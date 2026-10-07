import { api } from '@/api/client'
import { monthEnd, monthStart } from '@/lib/months'
import type { CategorySpend, PeriodSummary, TrendPoint, UnusualItem } from '@/types/api'

function range(month: string) {
  return { date_from: monthStart(month), date_to: monthEnd(month) }
}

export const insightsApi = {
  summary: (month: string) => api.get<PeriodSummary>('/insights/summary', range(month)),
  categories: (month: string) => api.get<CategorySpend[]>('/insights/categories', range(month)),
  trends: (months: number) => api.get<TrendPoint[]>('/insights/trends', { months }),
  unusual: (month: string) => api.get<UnusualItem[]>('/insights/unusual', { month: monthStart(month) }),
}