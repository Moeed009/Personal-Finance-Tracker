import { useState, type ChangeEvent, type FormEvent } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { Upload } from 'lucide-react'
import { importsApi } from '@/api/imports'
import { Button } from '@/components/Button'
import { SelectField } from '@/components/SelectField'
import { useAccounts } from '@/hooks/useAccounts'
import { formatBytes } from '@/lib/format'
import { invalidateFinanceData } from '@/lib/invalidate'
import { MAX_UPLOAD_MB, validateCsvFile } from '@/lib/imports'
import type { ImportSummary } from '@/types/api'

interface ImportUploadCardProps {
  onImported: (summary: ImportSummary) => void
}

export function ImportUploadCard({ onImported }: ImportUploadCardProps) {
  const queryClient = useQueryClient()
  const accounts = useAccounts()
  const accountList = accounts.data?.accounts ?? []

  const [accountId, setAccountId] = useState('')
  const [file, setFile] = useState<File | null>(null)
  const [fileError, setFileError] = useState<string | null>(null)
  const [inputKey, setInputKey] = useState(0)

  const selectedAccountId = accountId || (accountList.length === 1 ? accountList[0].id : '')
  const canSubmit = Boolean(file && selectedAccountId && !fileError)

  const mutation = useMutation({
    mutationFn: ({ file, accountId }: { file: File; accountId: string }) => importsApi.upload(file, accountId),
    onSuccess: async (summary) => {
      await invalidateFinanceData(queryClient)
      setFile(null)
      setInputKey((key) => key + 1)
      onImported(summary)
    },
  })

  const handleFileChange = (event: ChangeEvent<HTMLInputElement>) => {
    const selected = event.target.files?.[0] ?? null
    mutation.reset()
    setFile(selected)
    setFileError(selected ? validateCsvFile(selected) : null)
  }

  const handleSubmit = (event: FormEvent) => {
    event.preventDefault()
    if (file && selectedAccountId && !fileError) mutation.mutate({ file, accountId: selectedAccountId })
  }

  if (!accounts.isPending && accountList.length === 0) {
    return (
      <div className="rounded-xl bg-white p-6 shadow-sm ring-1 ring-slate-200">
        <p className="text-sm text-slate-600">You need an account before importing transactions.</p>
        <Link
          to="/accounts"
          className="mt-4 inline-flex items-center justify-center rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700"
        >
          Create account
        </Link>
      </div>
    )
  }

  return (
    <form onSubmit={handleSubmit} className="rounded-xl bg-white p-6 shadow-sm ring-1 ring-slate-200">
      <h2 className="text-base font-semibold text-slate-900">Upload a CSV</h2>
      <p className="mt-1 text-sm text-slate-500">Transactions are added to the account you choose.</p>

      <div className="mt-4 grid gap-4 sm:grid-cols-2">
        <SelectField label="Account" value={selectedAccountId} onChange={(event) => setAccountId(event.target.value)}>
          <option value="">Select account</option>
          {accountList.map((account) => (
            <option key={account.id} value={account.id}>
              {account.name}
            </option>
          ))}
        </SelectField>

        <div>
          <label htmlFor="csv-file" className="mb-1 block text-sm font-medium text-slate-700">
            CSV file
          </label>
          <input
            key={inputKey}
            id="csv-file"
            type="file"
            accept=".csv,text/csv"
            onChange={handleFileChange}
            className="block w-full text-sm text-slate-600 file:mr-4 file:rounded-lg file:border-0 file:bg-indigo-50 file:px-4 file:py-2 file:text-sm file:font-medium file:text-indigo-700 hover:file:bg-indigo-100"
          />
          {file && !fileError && <p className="mt-1 text-xs text-slate-500">{formatBytes(file.size)}</p>}
          {fileError && <p className="mt-1 text-xs text-rose-600">{fileError}</p>}
        </div>
      </div>

      {mutation.error && (
        <p className="mt-4 rounded-lg bg-rose-50 px-3 py-2 text-sm text-rose-700">{mutation.error.message}</p>
      )}

      <div className="mt-5">
        <Button type="submit" disabled={!canSubmit || mutation.isPending}>
          <Upload size={16} />
          {mutation.isPending ? 'Importing...' : 'Import transactions'}
        </Button>
      </div>

      <details className="mt-5 rounded-lg bg-slate-50 p-4 text-sm text-slate-600">
        <summary className="cursor-pointer font-medium text-slate-700">Supported CSV format</summary>
        <ul className="mt-3 list-disc space-y-1 pl-5">
          <li>
            The first row must be a header. Required columns: <strong>Date</strong>, <strong>Description</strong> and
            either <strong>Amount</strong> or <strong>Debit</strong>/<strong>Credit</strong>.
          </li>
          <li>With an Amount column, negative values are expenses and positive values are income.</li>
          <li>Optional columns: Type (Income/Expense) and Balance.</li>
          <li>Rows already imported (same date, amount and description) are skipped.</li>
          <li>Maximum file size is {MAX_UPLOAD_MB} MB.</li>
        </ul>
        <p className="mt-3 rounded-md bg-amber-50 px-3 py-2 text-amber-800">
          If your file has a Balance column, the account&apos;s opening balance is adjusted automatically so the
          balance matches your statement.
        </p>
      </details>
    </form>
  )
}