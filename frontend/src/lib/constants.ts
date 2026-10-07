import type { AccountType, CategoryType, TransactionType } from '@/types/api'

export const ACCOUNT_TYPES = ['CASH', 'BANK', 'WALLET'] as const satisfies readonly AccountType[]

export const ACCOUNT_TYPE_LABELS: Record<AccountType, string> = {
  CASH: 'Cash',
  BANK: 'Bank account',
  WALLET: 'Digital wallet',
}

export const CATEGORY_TYPES = ['INCOME', 'EXPENSE', 'BOTH'] as const satisfies readonly CategoryType[]

export const CATEGORY_TYPE_LABELS: Record<CategoryType, string> = {
  INCOME: 'Income',
  EXPENSE: 'Expense',
  BOTH: 'Income & Expense',
}

export const TRANSACTION_TYPES = ['INCOME', 'EXPENSE'] as const satisfies readonly TransactionType[]

export const TRANSACTION_TYPE_LABELS: Record<TransactionType, string> = {
  INCOME: 'Income',
  EXPENSE: 'Expense',
}