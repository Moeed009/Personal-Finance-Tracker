import { useQuery } from '@tanstack/react-query'
import { goalsApi } from '@/api/goals'

export const GOALS_KEY = ['goals'] as const

export function useGoals() {
  return useQuery({
    queryKey: GOALS_KEY,
    queryFn: goalsApi.list,
  })
}