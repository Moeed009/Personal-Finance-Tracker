import { api, type QueryParams } from '@/api/client'
import type { Page, Transaction, TransactionInput, TransactionPatch, TransferInput, TransferResult } from '@/types/api'

export const transactionsApi = {
  list: (params: QueryParams) => api.get<Page<Transaction>>('/transactions', params),
  create: (input: TransactionInput) => api.post<Transaction>('/transactions', input),
  update: (id: string, patch: TransactionPatch) => api.patch<Transaction>(`/transactions/${id}`, patch),
  remove: (id: string) => api.delete(`/transactions/${id}`),
  transfer: (input: TransferInput) => api.post<TransferResult>('/transfers', input),
}