import type { Category, TransactionType } from '@/types/api'

export function isCategoryCompatible(category: Category, transactionType: TransactionType): boolean {
  return category.type === 'BOTH' || category.type === transactionType
}