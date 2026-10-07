import { api } from '@/api/client'
import type { Category, CategoryInput } from '@/types/api'

export const categoriesApi = {
  list: () => api.get<Category[]>('/categories'),
  create: (input: CategoryInput) => api.post<Category>('/categories', input),
  rename: (id: string, name: string) => api.patch<Category>(`/categories/${id}`, { name }),
  remove: (id: string) => api.delete(`/categories/${id}`),
}