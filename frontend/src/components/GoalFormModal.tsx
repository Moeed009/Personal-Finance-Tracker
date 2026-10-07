import { useMemo } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { goalsApi } from '@/api/goals'
import { Button } from '@/components/Button'
import { Modal } from '@/components/Modal'
import { TextField } from '@/components/TextField'
import { GOALS_KEY } from '@/hooks/useGoals'
import { todayISO } from '@/lib/dates'
import { isoDate, positiveAmount } from '@/lib/validation'
import type { Goal, GoalStatus } from '@/types/api'

function buildSchema(isNew: boolean) {
  return z
    .object({
      name: z.string().trim().min(1, 'Name is required').max(120, 'Maximum 120 characters'),
      target_amount: positiveAmount,
      target_date: isoDate,
    })
    .refine((data) => !isNew || data.target_date >= todayISO(), {
      message: 'Target date cannot be in the past',
      path: ['target_date'],
    })
}

type FormValues = z.infer<ReturnType<typeof buildSchema>>

interface GoalFormModalProps {
  goal: Goal | null
  onClose: () => void
}

export function GoalFormModal({ goal, onClose }: GoalFormModalProps) {
  const queryClient = useQueryClient()
  const schema = useMemo(() => buildSchema(!goal), [goal])

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      name: goal?.name ?? '',
      target_amount: goal?.target_amount ?? '',
      target_date: goal?.target_date ?? '',
    },
  })

  const mutation = useMutation({
    mutationFn: (values: FormValues) => {
      if (!goal) return goalsApi.create(values)

      const reached = Number(goal.saved_amount) >= Number(values.target_amount)
      const status: GoalStatus = reached ? 'COMPLETED' : 'ACTIVE'
      return goalsApi.update(goal.id, { ...values, ...(status !== goal.status ? { status } : {}) })
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: GOALS_KEY })
      onClose()
    },
  })

  return (
    <Modal title={goal ? 'Edit goal' : 'Add goal'} onClose={onClose}>
      <form onSubmit={handleSubmit((values) => mutation.mutate(values))} className="space-y-4" noValidate>
        <TextField label="Goal name" placeholder="e.g. New laptop" error={errors.name?.message} {...register('name')} />
        <TextField
          label="Target amount"
          inputMode="decimal"
          error={errors.target_amount?.message}
          {...register('target_amount')}
        />
        <TextField label="Target date" type="date" error={errors.target_date?.message} {...register('target_date')} />

        {mutation.error && (
          <p className="rounded-lg bg-rose-50 px-3 py-2 text-sm text-rose-700">{mutation.error.message}</p>
        )}

        <div className="flex justify-end gap-2 pt-2">
          <Button variant="secondary" onClick={onClose}>
            Cancel
          </Button>
          <Button type="submit" disabled={mutation.isPending}>
            {mutation.isPending ? 'Saving...' : goal ? 'Save changes' : 'Create goal'}
          </Button>
        </div>
      </form>
    </Modal>
  )
}