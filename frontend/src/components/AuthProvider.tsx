import { useCallback, useEffect, useMemo, type ReactNode } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { ApiError, setUnauthorizedHandler } from '@/api/client'
import { authApi } from '@/api/auth'
import { AuthContext, ME_KEY, type AuthContextValue } from '@/lib/auth-context'
import type { LoginInput, User } from '@/types/api'

async function fetchMe(): Promise<User | null> {
  try {
    return await authApi.me()
  } catch (error) {
    if (error instanceof ApiError && error.status === 401) return null
    throw error
  }
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const queryClient = useQueryClient()

  const { data, isLoading } = useQuery({
    queryKey: ME_KEY,
    queryFn: fetchMe,
    staleTime: Infinity,
  })

  useEffect(() => {
    setUnauthorizedHandler(() => queryClient.setQueryData(ME_KEY, null))
    return () => setUnauthorizedHandler(null)
  }, [queryClient])

  const login = useCallback(
    async (input: LoginInput) => {
      await authApi.login(input)
      await queryClient.invalidateQueries({ queryKey: ME_KEY })
    },
    [queryClient],
  )

  const logout = useCallback(async () => {
    try {
      await authApi.logout()
    } finally {
      queryClient.removeQueries({ predicate: (query) => query.queryKey[0] !== ME_KEY[0] })
      queryClient.setQueryData(ME_KEY, null)
    }
  }, [queryClient])

  const value = useMemo<AuthContextValue>(
    () => ({ user: data ?? null, isLoading, login, logout }),
    [data, isLoading, login, logout],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}