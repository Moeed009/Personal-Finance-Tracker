import { api, request } from '@/api/client'
import type { LoginInput, RegisterInput, User } from '@/types/api'

export type ResetCredentials =
  | { kind: 'token_hash'; tokenHash: string }
  | { kind: 'session'; accessToken: string; refreshToken: string }

export const authApi = {
  login: (input: LoginInput) => api.post<unknown>('/auth/login', input, { skipAuthHandler: true }),
  register: (input: RegisterInput) => api.post<User>('/auth/register', input, { skipAuthHandler: true }),
  logout: () => api.post<void>('/auth/logout'),
  me: () => request<User>('/users', { skipAuthHandler: true }),
  forgotPassword: (email: string) =>
    api.post<{ message: string }>('/auth/forgot-password', { email }, { skipAuthHandler: true }),
  resetPassword: (credentials: ResetCredentials, newPassword: string) =>
    api.post<{ message: string }>(
      '/auth/reset-password',
      credentials.kind === 'token_hash'
        ? { token_hash: credentials.tokenHash, new_password: newPassword }
        : {
            access_token: credentials.accessToken,
            refresh_token: credentials.refreshToken,
            new_password: newPassword,
          },
      { skipAuthHandler: true },
    ),
}