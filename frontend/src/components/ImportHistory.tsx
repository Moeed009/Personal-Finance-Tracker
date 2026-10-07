import { useMutation } from '@tanstack/react-query'
import { Download, Eye, FileSpreadsheet } from 'lucide-react'
import { importsApi } from '@/api/imports'
import { formatBytes, formatDate } from '@/lib/format'
import type { Account, ImportBatch } from '@/types/api'

interface ImportHistoryProps {
  batches: ImportBatch[]
  accounts: Map<string, Account>
  onView: (batch: ImportBatch) => void
}

function DownloadButton({ batch }: { batch: ImportBatch }) {
  const mutation = useMutation({
    mutationFn: () => importsApi.downloadLink(batch.id),
    onSuccess: ({ url }) => {
      const link = document.createElement('a')
      link.href = url
      link.target = '_blank'
      link.rel = 'noopener noreferrer'
      document.body.appendChild(link)
      link.click()
      link.remove()
    },
  })

  return (
    <>
      <button
        onClick={() => mutation.mutate()}
        disabled={mutation.isPending}
        className="rounded-md p-2 text-slate-400 hover:bg-slate-100 hover:text-slate-700 disabled:opacity-50"
        aria-label={`Download ${batch.filename}`}
        title={mutation.error?.message ?? 'Download original CSV'}
      >
        <Download size={16} />
      </button>
      {mutation.error && <span className="ml-1 text-xs text-rose-600">Failed</span>}
    </>
  )
}

export function ImportHistory({ batches, accounts, onView }: ImportHistoryProps) {
  if (batches.length === 0) {
    return (
      <div className="rounded-xl border border-dashed border-slate-300 bg-white p-10 text-center">
        <FileSpreadsheet className="mx-auto text-slate-400" size={32} />
        <p className="mt-3 font-medium text-slate-900">No imports yet</p>
        <p className="mt-1 text-sm text-slate-500">Your uploaded files will be listed here.</p>
      </div>
    )
  }

  return (
    <div className="overflow-hidden rounded-xl bg-white shadow-sm ring-1 ring-slate-200">
      <div className="overflow-x-auto">
        <table className="w-full min-w-[720px] text-left text-sm">
          <thead className="border-b border-slate-100 text-xs uppercase tracking-wide text-slate-500">
            <tr>
              <th className="px-4 py-3 font-medium">File</th>
              <th className="px-4 py-3 font-medium">Account</th>
              <th className="px-4 py-3 font-medium">Imported on</th>
              <th className="px-4 py-3 font-medium">Rows</th>
              <th className="px-4 py-3">
                <span className="sr-only">Actions</span>
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {batches.map((batch) => (
              <tr key={batch.id} className="hover:bg-slate-50">
                <td className="px-4 py-3">
                  <p className="font-medium text-slate-900">{batch.filename}</p>
                  <p className="text-xs text-slate-500">{formatBytes(batch.file_size)}</p>
                </td>
                <td className="px-4 py-3 text-slate-600">{accounts.get(batch.account_id)?.name ?? '—'}</td>
                <td className="whitespace-nowrap px-4 py-3 text-slate-600">{formatDate(batch.created_at)}</td>
                <td className="px-4 py-3">
                  <div className="flex flex-wrap gap-1.5 text-xs font-medium">
                    <span className="rounded-full bg-emerald-50 px-2 py-0.5 text-emerald-700">
                      {batch.rows_imported} imported
                    </span>
                    {batch.rows_skipped > 0 && (
                      <span className="rounded-full bg-amber-50 px-2 py-0.5 text-amber-700">
                        {batch.rows_skipped} skipped
                      </span>
                    )}
                    {batch.rows_failed > 0 && (
                      <span className="rounded-full bg-rose-50 px-2 py-0.5 text-rose-700">
                        {batch.rows_failed} failed
                      </span>
                    )}
                  </div>
                </td>
                <td className="whitespace-nowrap px-4 py-3 text-right">
                  <button
                    onClick={() => onView(batch)}
                    className="rounded-md p-2 text-slate-400 hover:bg-slate-100 hover:text-slate-700"
                    aria-label={`View transactions from ${batch.filename}`}
                    title="View imported transactions"
                  >
                    <Eye size={16} />
                  </button>
                  <DownloadButton batch={batch} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}