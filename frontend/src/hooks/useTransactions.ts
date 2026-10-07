import { keepPreviousData, useQuery } from '@tanstack/react-query'
import { transactionsApi } from '@/api/transactions'
import type { TransactionFilters } from '@/lib/transaction-filters'

export const TRANSACTIONS_KEY = ['transactions'] as const
export const TRANSACTIONS_PAGE_SIZE = 20

export function useTransactions(filters: TransactionFilters) {
  return useQuery({
    queryKey: [...TRANSACTIONS_KEY, 'list', filters],
    queryFn: () => transactionsApi.list({ ...filters, page_size: TRANSACTIONS_PAGE_SIZE }),
    placeholderData: keepPreviousData,
  })
}