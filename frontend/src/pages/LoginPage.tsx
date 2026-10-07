import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useMutation } from '@tanstack/react-query'
import { Link, useLocation } from 'react-router-dom'

import { AuthCard } from '@/components/AuthCard'
import { TextField } from '@/components/TextField'
import { useAuth } from '@/hooks/useAuth'

const schema = z.object({
  email: z.email('Enter a valid email address'),
  password: z.string().min(1, 'Password is required'),
})

type LoginForm = z.infer<typeof schema>

export default function LoginPage() {
  const { login } = useAuth()
  const location = useLocation()

  const registered = (
    location.state as { registered?: boolean } | null
  )?.registered

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginForm>({
    resolver: zodResolver(schema),
  })

  const mutation = useMutation({
    mutationFn: login,
  })

  return (
    <AuthCard
      title="Welcome back"
      subtitle="Log in to your Personal Finance Tracker"
      footer={
        <>
          No account yet?{' '}
          <Link
            to="/register"
            className="font-medium text-indigo-600 hover:underline"
          >
            Create one
          </Link>
        </>
      }
    >
      {registered && (
        <p className="mb-4 rounded-lg bg-emerald-50 px-3 py-2 text-sm text-emerald-700">
          Account created. Please log in.
        </p>
      )}

      <form
        onSubmit={handleSubmit((values) => mutation.mutate(values))}
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

        <TextField
          label="Password"
          type="password"
          autoComplete="current-password"
          error={errors.password?.message}
          {...register('password')}
        />

        <div className="flex justify-end">
          <Link
            to="/forgot-password"
            className="text-sm font-medium text-indigo-600 hover:underline"
          >
            Forgot password?
          </Link>
        </div>

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
          {mutation.isPending ? 'Logging in...' : 'Log in'}
        </button>
      </form>
    </AuthCard>
  )
}