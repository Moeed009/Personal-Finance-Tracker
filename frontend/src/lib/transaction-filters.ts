import type { TransactionType } from '@/types/api'

export type TransactionFilters = {
  search: string
  type: '' | TransactionType
  account_id: string
  category_id: string
  date_from: string
  date_to: string
  page: number
}

export type FilterPatch = Partial<Record<Exclude<keyof TransactionFilters, 'type' | 'page'> | 'type' | 'page', string>>

export function parseFilters(params: URLSearchParams): TransactionFilters {
  const type = params.get('type')
  const page = Number(params.get('page'))

  return {
    search: params.get('search') ?? '',
    type: type === 'INCOME' || type === 'EXPENSE' ? type : '',
    account_id: params.get('account_id') ?? '',
    category_id: params.get('category_id') ?? '',
    date_from: params.get('date_from') ?? '',
    date_to: params.get('date_to') ?? '',
    page: Number.isInteger(page) && page >= 1 ? page : 1,
  }
}

export function hasActiveFilters(filters: TransactionFilters): boolean {
  return Boolean(
    filters.search || filters.type || filters.account_id || filters.category_id || filters.date_from || filters.date_to,
  )
}