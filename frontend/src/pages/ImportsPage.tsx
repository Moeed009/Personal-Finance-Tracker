import { useMemo, useState } from 'react'
import { Button } from '@/components/Button'
import { ImportBatchTransactionsModal } from '@/components/ImportBatchTransactionsModal'
import { ImportHistory } from '@/components/ImportHistory'
import { ImportSummaryCard } from '@/components/ImportSummaryCard'
import { ImportUploadCard } from '@/components/ImportUploadCard'
import { PageHeader } from '@/components/PageHeader'
import { useAccounts } from '@/hooks/useAccounts'
import { useAuth } from '@/hooks/useAuth'
import { useImportBatches } from '@/hooks/useImports'
import type { ImportBatch, ImportSummary } from '@/types/api'

export default function ImportsPage() {
  const { user } = useAuth()
  const currency = user?.currency ?? 'PKR'

  const batches = useImportBatches()
  const accounts = useAccounts()
  const [summary, setSummary] = useState<ImportSummary | null>(null)
  const [viewing, setViewing] = useState<ImportBatch | null>(null)

  const accountMap = useMemo(
    () => new Map((accounts.data?.accounts ?? []).map((account) => [account.id, account] as const)),
    [accounts.data],
  )

  return (
    <>
      <PageHeader title="CSV Import" description="Bring in transactions from your bank statement" />

      <ImportUploadCard onImported={setSummary} />
      {summary && <ImportSummaryCard summary={summary} onDismiss={() => setSummary(null)} />}

      <h2 className="mb-3 mt-8 text-base font-semibold text-slate-900">Import history</h2>

      {batches.isPending && <div className="h-32 animate-pulse rounded-xl bg-slate-200" />}

      {batches.error && (
        <div className="rounded-xl bg-rose-50 p-5 text-sm text-rose-700">
          <p>{batches.error.message}</p>
          <Button variant="secondary" className="mt-3" onClick={() => batches.refetch()}>
            Try again
          </Button>
        </div>
      )}

      {batches.data && <ImportHistory batches={batches.data} accounts={accountMap} onView={setViewing} />}

      {viewing && (
        <ImportBatchTransactionsModal batch={viewing} currency={currency} onClose={() => setViewing(null)} />
      )}
    </>
  )
}