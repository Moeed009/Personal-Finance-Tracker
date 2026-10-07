import { useEffect, useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useMutation } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { authApi, type ResetCredentials } from '@/api/auth'
import { AuthCard } from '@/components/AuthCard'
import { TextField } from '@/components/TextField'

const schema = z
  .object({
    password: z.string().min(8, 'Minimum 8 characters').max(72, 'Maximum 72 characters'),
    confirmPassword: z.string(),
  })
  .refine((data) => data.password === data.confirmPassword, {
    message: 'Passwords do not match',
    path: ['confirmPassword'],
  })

type ResetForm = z.infer<typeof schema>

type ResetLink = ResetCredentials | { kind: 'invalid'; reason?: string }

function readResetLink(): ResetLink {
  const query = new URLSearchParams(window.location.search)
  const hash = new URLSearchParams(window.location.hash.replace(/^#/, ''))

  const tokenHash = query.get('token_hash')
  if (tokenHash) return { kind: 'token_hash', tokenHash }

  const accessToken = hash.get('access_token')
  const refreshToken = hash.get('refresh_token')
  if (accessToken && refreshToken) return { kind: 'session', accessToken, refreshToken }

  return { kind: 'invalid', reason: hash.get('error_description') ?? undefined }
}

const linkClass = 'font-medium text-indigo-600 hover:underline'
const buttonLinkClass =
  'inline-flex w-full items-center justify-center rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white transition hover:bg-indigo-700'

export default function ResetPasswordPage() {
  const [link] = useState(readResetLink)

  useEffect(() => {
    if (window.location.hash) {
      window.history.replaceState(null, '', window.location.pathname + window.location.search)
    }
  }, [])

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<ResetForm>({ resolver: zodResolver(schema) })

  const mutation = useMutation({
    mutationFn: (password: string) => {
      if (link.kind === 'invalid') throw new Error('This reset link is invalid or has expired.')
      return authApi.resetPassword(link, password)
    },
  })

  if (link.kind === 'invalid') {
    return (
      <AuthCard
        title="Invalid reset link"
        subtitle={link.reason ?? 'This password reset link is invalid or has expired.'}
        footer={
          <Link to="/login" className={linkClass}>
            Back to log in
          </Link>
        }
      >
        <Link to="/forgot-password" className={buttonLinkClass}>
          Request a new reset link
        </Link>
      </AuthCard>
    )
  }

  if (mutation.isSuccess) {
    return (
      <AuthCard
        title="Password updated"
        subtitle="Your password has been changed. You can now log in with the new password."
        footer={null}
      >
        <Link to="/login" className={buttonLinkClass}>
          Go to log in
        </Link>
      </AuthCard>
    )
  }

  return (
    <AuthCard
      title="Choose a new password"
      subtitle="Enter a new password for your account"
      footer={
        <Link to="/login" className={linkClass}>
          Back to log in
        </Link>
      }
    >
      <form onSubmit={handleSubmit((values) => mutation.mutate(values.password))} className="space-y-4" noValidate>
        <TextField
          label="New password"
          type="password"
          autoComplete="new-password"
          error={errors.password?.message}
          {...register('password')}
        />
        <TextField
          label="Confirm new password"
          type="password"
          autoComplete="new-password"
          error={errors.confirmPassword?.message}
          {...register('confirmPassword')}
        />

        {mutation.error && (
          <div className="rounded-lg bg-rose-50 px-3 py-2 text-sm text-rose-700">
            <p>{mutation.error.message}</p>
            <Link to="/forgot-password" className="mt-1 inline-block font-medium underline">
              Request a new reset link
            </Link>
          </div>
        )}

        <button
          type="submit"
          disabled={mutation.isPending}
          className="w-full rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white transition hover:bg-indigo-700 disabled:opacity-60"
        >
          {mutation.isPending ? 'Updating...' : 'Update password'}
        </button>
      </form>
    </AuthCard>
  )
}