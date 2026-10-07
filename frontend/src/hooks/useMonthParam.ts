import { useCallback } from 'react'
import { useSearchParams } from 'react-router-dom'
import { currentMonth, isValidMonth } from '@/lib/months'

export function useMonthParam(): [string, (month: string) => void] {
  const [searchParams, setSearchParams] = useSearchParams()
  const param = searchParams.get('month')
  const month = isValidMonth(param) ? param : currentMonth()

  const setMonth = useCallback(
    (next: string) => setSearchParams({ month: next }, { replace: true }),
    [setSearchParams],
  )

  return [month, setMonth]
}