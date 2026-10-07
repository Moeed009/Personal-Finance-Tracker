import { useQuery } from '@tanstack/react-query'
import { accountsApi } from '@/api/accounts'

export const ACCOUNTS_KEY = ['accounts'] as const

export function useAccounts() {
  return useQuery({
    queryKey: [...ACCOUNTS_KEY, 'summary'],
    queryFn: accountsApi.summary,
  })
}