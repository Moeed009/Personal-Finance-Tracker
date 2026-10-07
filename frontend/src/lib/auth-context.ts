import { createContext } from 'react'
import type { LoginInput, User } from '@/types/api'

export const ME_KEY = ['me'] as const

export interface AuthContextValue {
  user: User | null
  isLoading: boolean
  login: (input: LoginInput) => Promise<void>
  logout: () => Promise<void>
}

export const AuthContext = createContext<AuthContextValue | null>(null)