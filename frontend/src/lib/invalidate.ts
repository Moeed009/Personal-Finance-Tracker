import type { QueryClient } from '@tanstack/react-query'

const KEEP = new Set(['me', 'categories'])

export function invalidateFinanceData(queryClient: QueryClient) {
  return queryClient.invalidateQueries({
    predicate: (query) => !KEEP.has(String(query.queryKey[0])),
  })
}