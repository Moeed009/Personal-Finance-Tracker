import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useMutation } from '@tanstack/react-query'
import { Link } from 'react-router-dom'

import { authApi } from '@/api/auth'
import { AuthCard } from '@/components/AuthCard'
import { TextField } from '@/components/TextField'

const schema = z.object({
  email: z.email('Enter a valid email address'),
})

type ForgotPasswordForm = z.infer<typeof schema>

export default function ForgotPasswordPage() {
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<ForgotPasswordForm>({
    resolver: zodResolver(schema),
  })

  const mutation = useMutation({
    mutationFn: authApi.forgotPassword,
  })

  const onSubmit = (values: ForgotPasswordForm) => {
    mutation.mutate(values.email)
  }

  return (
    <AuthCard
      title="Forgot your password?"
      subtitle="Enter your email and we'll send you a password reset link."
      footer={
        <>
          Remember your password?{' '}
          <Link
            to="/login"
            className="font-medium text-indigo-600 hover:underline"
          >
            Log in
          </Link>
        </>
      }
    >
      {mutation.isSuccess ? (
        <div className="space-y-4">
          <p className="rounded-lg bg-emerald-50 px-3 py-2 text-sm text-emerald-700">
            If an account exists for this email, a reset link has been sent.
            Please check your inbox.
          </p>

          <Link
            to="/login"
            className="block w-full rounded-lg bg-indigo-600 px-4 py-2 text-center text-sm font-medium text-white transition hover:bg-indigo-700"
          >
            Back to login
          </Link>
        </div>
      ) : (
        <form
          onSubmit={handleSubmit(onSubmit)}
          className="space-y-4"
          noValidate
        >
          <TextField
            label="Email"
            type="email"
            autoComplete="email"
            error={errors.email?.message}
            {...register('email')}
          />

          {mutation.error && (
            <p className="rounded-lg bg-rose-50 px-3 py-2 text-sm text-rose-700">
              {mutation.error.message}
            </p>
          )}

          <button
            type="submit"
            disabled={mutation.isPending}
            className="w-full rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white transition hover:bg-indigo-700 disabled:opacity-60"
          >
            {mutation.isPending ? 'Sending...' : 'Send reset link'}
          </button>
        </form>
      )}
    </AuthCard>
  )
}