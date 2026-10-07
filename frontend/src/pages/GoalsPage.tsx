import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { CheckCircle2, PiggyBank, Plus, Target } from 'lucide-react'
import { goalsApi } from '@/api/goals'
import { Button } from '@/components/Button'
import { ConfirmDialog } from '@/components/ConfirmDialog'
import { ContributeModal } from '@/components/ContributeModal'
import { GoalCard } from '@/components/GoalCard'
import { GoalFormModal } from '@/components/GoalFormModal'
import { PageHeader } from '@/components/PageHeader'
import { StatCard } from '@/components/StatCard'
import { GOALS_KEY, useGoals } from '@/hooks/useGoals'
import { useAuth } from '@/hooks/useAuth'
import { formatMoney } from '@/lib/format'
import type { Goal } from '@/types/api'

function DeleteGoalDialog({ goal, onClose }: { goal: Goal; onClose: () => void }) {
  const queryClient = useQueryClient()

  const mutation = useMutation({
    mutationFn: () => goalsApi.remove(goal.id),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: GOALS_KEY })
      onClose()
    },
  })

  return (
    <ConfirmDialog
      title="Delete goal"
      message={
        <>
          Delete <span className="font-medium text-slate-900">{goal.name}</span>? Its saved progress will be lost.
        </>
      }
      confirmLabel="Delete"
      pendingLabel="Deleting..."
      isPending={mutation.isPending}
      error={mutation.error?.message}
      onConfirm={() => mutation.mutate()}
      onClose={onClose}
    />
  )
}

export default function GoalsPage() {
  const { user } = useAuth()
  const currency = user?.currency ?? 'PKR'

  const { data, isLoading, error, refetch } = useGoals()
  const [editing, setEditing] = useState<Goal | 'new' | null>(null)
  const [contributing, setContributing] = useState<Goal | null>(null)
  const [deleting, setDeleting] = useState<Goal | null>(null)

  const goals = data ?? []
  const active = goals.filter((goal) => goal.status === 'ACTIVE')
  const completed = goals.filter((goal) => goal.status === 'COMPLETED')
  const totalSaved = goals.reduce((sum, goal) => sum + Number(goal.saved_amount), 0)
  const totalRemaining = active.reduce((sum, goal) => sum + Number(goal.remaining_amount), 0)

  const renderCard = (goal: Goal) => (
    <GoalCard
      key={goal.id}
      goal={goal}
      currency={currency}
      onContribute={() => setContributing(goal)}
      onEdit={() => setEditing(goal)}
      onDelete={() => setDeleting(goal)}
    />
  )

  return (
    <>
      <PageHeader
        title="Goals"
        description="Save towards the things that matter"
        actions={
          <Button onClick={() => setEditing('new')}>
            <Plus size={16} />
            Add goal
          </Button>
        }
      />

      {isLoading && (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {[0, 1, 2].map((item) => (
            <div key={item} className="h-44 animate-pulse rounded-xl bg-slate-200" />
          ))}
        </div>
      )}

      {error && (
        <div className="rounded-xl bg-rose-50 p-5 text-sm text-rose-700">
          <p>{error.message}</p>
          <Button variant="secondary" className="mt-3" onClick={() => refetch()}>
            Try again
          </Button>
        </div>
      )}

      {data && goals.length === 0 && (
        <div className="rounded-xl border border-dashed border-slate-300 bg-white p-10 text-center">
          <Target className="mx-auto text-slate-400" size={32} />
          <p className="mt-3 font-medium text-slate-900">No goals yet</p>
          <p className="mt-1 text-sm text-slate-500">Create a goal with a target amount and date to start saving.</p>
          <Button className="mt-4" onClick={() => setEditing('new')}>
            <Plus size={16} />
            Add goal
          </Button>
        </div>
      )}

      {data && goals.length > 0 && (
        <>
          <div className="mb-8 grid gap-4 sm:grid-cols-3">
            <StatCard label="Active goals" icon={Target} value={String(active.length)} hint={`${completed.length} completed`} />
            <StatCard label="Total saved" icon={PiggyBank} tone="positive" value={formatMoney(totalSaved, currency)} />
            <StatCard label="Still to save" icon={CheckCircle2} value={formatMoney(totalRemaining, currency)} hint="Across active goals" />
          </div>

          {active.length > 0 && (
            <section className="mb-8">
              <h2 className="mb-3 text-base font-semibold text-slate-900">In progress</h2>
              <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">{active.map(renderCard)}</div>
            </section>
          )}

          {completed.length > 0 && (
            <section>
              <h2 className="mb-3 text-base font-semibold text-slate-900">Completed</h2>
              <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">{completed.map(renderCard)}</div>
            </section>
          )}
        </>
      )}

      {editing && <GoalFormModal goal={editing === 'new' ? null : editing} onClose={() => setEditing(null)} />}
      {contributing && <ContributeModal goal={contributing} currency={currency} onClose={() => setContributing(null)} />}
      {deleting && <DeleteGoalDialog goal={deleting} onClose={() => setDeleting(null)} />}
    </>
  )
}