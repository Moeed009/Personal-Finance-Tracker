import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { goalsApi } from '@/api/goals'
import { Button } from '@/components/Button'
import { Modal } from '@/components/Modal'
import { TextField } from '@/components/TextField'
import { GOALS_KEY } from '@/hooks/useGoals'
import { formatMoney } from '@/lib/format'
import { positiveAmount } from '@/lib/validation'
import type { Goal } from '@/types/api'

const schema = z.object({ amount: positiveAmount })

type FormValues = z.infer<typeof schema>

interface ContributeModalProps {
  goal: Goal
  currency: string
  onClose: () => void
}

export function ContributeModal({ goal, currency, onClose }: ContributeModalProps) {
  const queryClient = useQueryClient()

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<FormValues>({ resolver: zodResolver(schema), defaultValues: { amount: '' } })

  const mutation = useMutation({
    mutationFn: (values: FormValues) => goalsApi.contribute(goal.id, values.amount),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: GOALS_KEY })
      onClose()
    },
  })

  return (
    <Modal title="Add savings" onClose={onClose}>
      <form onSubmit={handleSubmit((values) => mutation.mutate(values))} className="space-y-4" noValidate>
        <div className="text-sm text-slate-600">
          <p className="font-medium text-slate-900">{goal.name}</p>
          <p>{formatMoney(goal.remaining_amount, currency)} left to reach your target.</p>
        </div>

        <TextField label="Amount" inputMode="decimal" error={errors.amount?.message} {...register('amount')} />

        <p className="rounded-lg bg-amber-50 px-3 py-2 text-xs text-amber-800">
          This only updates the goal&apos;s progress. It does not move money out of any account, and it cannot be
          undone later.
        </p>

        {mutation.error && (
          <p className="rounded-lg bg-rose-50 px-3 py-2 text-sm text-rose-700">{mutation.error.message}</p>
        )}

        <div className="flex justify-end gap-2 pt-2">
          <Button variant="secondary" onClick={onClose}>
            Cancel
          </Button>
          <Button type="submit" disabled={mutation.isPending}>
            {mutation.isPending ? 'Saving...' : 'Add savings'}
          </Button>
        </div>
      </form>
    </Modal>
  )
}