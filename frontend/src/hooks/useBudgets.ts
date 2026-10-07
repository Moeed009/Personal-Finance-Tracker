import { useQuery } from '@tanstack/react-query'
import { budgetsApi } from '@/api/budgets'

export const BUDGETS_KEY = ['budgets'] as const

export function useBudgets(month: string) {
  return useQuery({
    queryKey: [...BUDGETS_KEY, month],
    queryFn: () => budgetsApi.list(month),
  })
}