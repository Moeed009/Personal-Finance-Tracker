import { api } from '@/api/client'
import type { User, UserUpdateInput } from '@/types/api'

export const usersApi = {
  update: (input: UserUpdateInput) => api.patch<User>('/users', input),
  remove: () => api.delete('/users'),
}