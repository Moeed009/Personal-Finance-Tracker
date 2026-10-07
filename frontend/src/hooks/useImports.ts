import { keepPreviousData, useQuery } from '@tanstack/react-query'
import { importsApi } from '@/api/imports'

export const IMPORTS_KEY = ['imports'] as const
export const IMPORT_TRANSACTIONS_PAGE_SIZE = 20

export function useImportBatches() {
  return useQuery({
    queryKey: IMPORTS_KEY,
    queryFn: importsApi.list,
  })
}

export function useImportBatchTransactions(batchId: string, page: number) {
  return useQuery({
    queryKey: [...IMPORTS_KEY, batchId, 'transactions', page],
    queryFn: () => importsApi.transactions(batchId, page, IMPORT_TRANSACTIONS_PAGE_SIZE),
    placeholderData: keepPreviousData,
  })
}