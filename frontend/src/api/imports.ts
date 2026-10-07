import { api } from '@/api/client'
import type { DownloadLink, ImportBatch, ImportedTransaction, ImportSummary, Page } from '@/types/api'

export const importsApi = {
  upload: (file: File, accountId: string) => {
    const body = new FormData()
    body.append('file', file)
    body.append('account_id', accountId)
    return api.post<ImportSummary>('/transactions/import', body)
  },
  list: () => api.get<ImportBatch[]>('/imports'),
  transactions: (batchId: string, page: number, pageSize: number) =>
    api.get<Page<ImportedTransaction>>(`/imports/${batchId}/transactions`, { page, page_size: pageSize }),
  downloadLink: (batchId: string) => api.get<DownloadLink>(`/imports/${batchId}/download`),
}