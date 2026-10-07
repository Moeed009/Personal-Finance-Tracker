import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { usersApi } from '@/api/users'
import { Button } from '@/components/Button'
import { DeleteProfileDialog } from '@/components/DeleteProfileDialog'
import { PageHeader } from '@/components/PageHeader'
import { SelectField } from '@/components/SelectField'
import { TextField } from '@/components/TextField'
import { useAuth } from '@/hooks/useAuth'
import { ME_KEY } from '@/lib/auth-context'
import { CURRENCIES } from '@/lib/currencies'
import type { User } from '@/types/api'

const schema = z.object({
  full_name: z.string().trim().min(1, 'Name is required').max(150, 'Maximum 150 characters'),
  currency: z.string().length(3, 'Select a currency'),
})

const passwordSchema = z
  .object({
    current_password: z.string().min(1, 'Current password is required'),
    new_password: z
      .string()
      .min(8, 'Password must be at least 8 characters')
      .max(72, 'Password must not exceed 72 characters'),
    confirm_password: z.string().min(1, 'Please confirm your new password'),
  })
  .refine((data) => data.new_password === data.confirm_password, {
    message: 'Passwords do not match',
    path: ['confirm_password'],
  })

type FormValues = z.infer<typeof schema>
type PasswordFormValues = z.infer<typeof passwordSchema>

function ProfileCard({ user }: { user: User }) {
  const queryClient = useQueryClient()

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isDirty },
  } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: { full_name: user.full_name, currency: user.currency },
  })

  const mutation = useMutation({
    mutationFn: (values: FormValues) => usersApi.update(values),
    onSuccess: (updated) => {
      queryClient.setQueryData(ME_KEY, updated)
      reset({ full_name: updated.full_name, currency: updated.currency })
    },
  })

  const options = CURRENCIES.some((currency) => currency.code === user.currency)
    ? CURRENCIES
    : [{ code: user.currency, label: user.currency }, ...CURRENCIES]

  return (
    <form
      onSubmit={handleSubmit((values) => mutation.mutate(values))}
      className="rounded-xl bg-white p-6 shadow-sm ring-1 ring-slate-200"
      noValidate
    >
      <h2 className="text-base font-semibold text-slate-900">Profile</h2>

      <div className="mt-4 grid gap-4 sm:grid-cols-2">
        <TextField
          label="Full name"
          autoComplete="name"
          error={errors.full_name?.message}
          {...register('full_name')}
        />

        <TextField
          label="Email"
          value={user.email}
          disabled
          readOnly
          className="bg-slate-50 text-slate-500"
        />
      </div>

      <div className="mt-4 max-w-xs">
        <SelectField
          label="Currency"
          error={errors.currency?.message}
          {...register('currency')}
        >
          {options.map((currency) => (
            <option key={currency.code} value={currency.code}>
              {currency.code} - {currency.label}
            </option>
          ))}
        </SelectField>
      </div>

      <p className="mt-2 text-xs text-amber-700">
        Changing the currency only changes how amounts are labelled. Existing amounts are not converted.
      </p>

      {mutation.error && (
        <p className="mt-4 rounded-lg bg-rose-50 px-3 py-2 text-sm text-rose-700">
          {mutation.error.message}
        </p>
      )}

      <div className="mt-5 flex items-center gap-3">
        <Button type="submit" disabled={!isDirty || mutation.isPending}>
          {mutation.isPending ? 'Saving...' : 'Save changes'}
        </Button>

        {mutation.isSuccess && !isDirty && (
          <span className="text-sm text-emerald-600">Saved</span>
        )}
      </div>
    </form>
  )
}

function PasswordCard() {
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isDirty },
  } = useForm<PasswordFormValues>({
    resolver: zodResolver(passwordSchema),
    defaultValues: {
      current_password: '',
      new_password: '',
      confirm_password: '',
    },
  })

  const mutation = useMutation({
    mutationFn: (values: PasswordFormValues) =>
      usersApi.update({
        current_password: values.current_password,
        new_password: values.new_password,
      }),
    onSuccess: () => {
      reset()
    },
  })

  return (
    <form
      onSubmit={handleSubmit((values) => mutation.mutate(values))}
      className="mt-6 rounded-xl bg-white p-6 shadow-sm ring-1 ring-slate-200"
      noValidate
    >
      <h2 className="text-base font-semibold text-slate-900">Security</h2>

      <p className="mt-1 text-sm text-slate-600">
        Change your password to keep your account secure.
      </p>

      <div className="mt-4 grid gap-4 sm:max-w-md">
        <TextField
          label="Current password"
          type="password"
          autoComplete="current-password"
          error={errors.current_password?.message}
          {...register('current_password')}
        />

        <TextField
          label="New password"
          type="password"
          autoComplete="new-password"
          error={errors.new_password?.message}
          {...register('new_password')}
        />

        <TextField
          label="Confirm new password"
          type="password"
          autoComplete="new-password"
          error={errors.confirm_password?.message}
          {...register('confirm_password')}
        />
      </div>

      <p className="mt-3 text-xs text-slate-500">
        Password must be between 8 and 72 characters.
      </p>

      {mutation.error && (
        <p className="mt-4 rounded-lg bg-rose-50 px-3 py-2 text-sm text-rose-700">
          {mutation.error.message}
        </p>
      )}

      {mutation.isSuccess && (
        <p className="mt-4 rounded-lg bg-emerald-50 px-3 py-2 text-sm text-emerald-700">
          Password updated successfully.
        </p>
      )}

      <div className="mt-5">
        <Button type="submit" disabled={!isDirty || mutation.isPending}>
          {mutation.isPending ? 'Updating...' : 'Change password'}
        </Button>
      </div>
    </form>
  )
}

export default function SettingsPage() {
  const { user } = useAuth()
  const [deleteOpen, setDeleteOpen] = useState(false)

  return (
    <>
      <PageHeader title="Settings" description="Manage your profile and account" />

      {user && <ProfileCard user={user} />}

      <PasswordCard />

      <section className="mt-6 rounded-xl bg-white p-6 shadow-sm ring-1 ring-rose-200">
        <h2 className="text-base font-semibold text-rose-700">Danger zone</h2>

        <p className="mt-1 text-sm text-slate-600">
          Delete your account and all of its data. You can undo this by logging in again within the grace period.
        </p>

        <Button
          variant="danger"
          className="mt-4"
          onClick={() => setDeleteOpen(true)}
        >
          Delete account
        </Button>
      </section>

      {deleteOpen && (
        <DeleteProfileDialog onClose={() => setDeleteOpen(false)} />
      )}
    </>
  )
}
