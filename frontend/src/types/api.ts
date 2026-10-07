export interface User {
  id: string
  email: string
  full_name: string
  currency: string
}

export interface LoginInput {
  email: string
  password: string
}

export interface RegisterInput {
  email: string
  password: string
  full_name: string
}

export type AccountType = 'CASH' | 'BANK' | 'WALLET'

export interface Account {
  id: string
  name: string
  type: AccountType
  opening_balance: string
  balance: string
  created_at: string
}

export interface AccountSummary {
  accounts: Account[]
  total_balance: string
}

export interface AccountInput {
  name: string
  type: AccountType
  opening_balance: string
}

export type CategoryType = 'INCOME' | 'EXPENSE' | 'BOTH'
export type TransactionType = 'INCOME' | 'EXPENSE'

export interface Category {
  id: string
  name: string
  type: CategoryType
  is_default: boolean
}

export interface CategoryInput {
  name: string
  type: CategoryType
}

export interface Transaction {
  id: string
  account_id: string
  category_id: string | null
  import_batch_id: string | null
  type: TransactionType
  amount: string
  description: string
  merchant: string | null
  transaction_date: string
  transfer_group_id: string | null
  is_recurring: boolean
  created_at: string
}

export interface Page<T> {
  items: T[]
  total: number
  page: number
  page_size: number
}
export interface TransactionInput {
  account_id: string
  type: TransactionType
  amount: string
  transaction_date: string
  description: string
  category_id?: string | null
  merchant?: string | null
}

export type TransactionPatch = Partial<TransactionInput>

export interface TransferInput {
  from_account_id: string
  to_account_id: string
  amount: string
  transaction_date: string
  description: string
}

export interface TransferResult {
  transfer_group_id: string
  outgoing: Transaction
  incoming: Transaction
}


export interface ImportError {
  row: number
  message: string
}

export interface ImportSummary {
  batch_id: string
  filename: string
  rows_total: number
  rows_imported: number
  rows_skipped: number
  rows_failed: number
  errors: ImportError[]
}

export interface ImportBatch {
  id: string
  account_id: string
  filename: string
  file_size: number
  rows_total: number
  rows_imported: number
  rows_skipped: number
  rows_failed: number
  created_at: string
}

export interface ImportedTransaction extends Transaction {
  dedupe_hash: string | null
  raw_data: Record<string, unknown> | null
}

export interface DownloadLink {
  url: string
  expires_in: number
}


export type BudgetStatus = 'ON_TRACK' | 'WARNING' | 'EXCEEDED'

export interface Budget {
  id: string
  category_id: string
  category_name: string
  month: string
  limit_amount: string
  spent: string
  remaining: string
  percent_used: string
  status: BudgetStatus
}

export interface BudgetInput {
  category_id: string
  month: string
  limit_amount: string
}

export interface PeriodSummary {
  start_date: string
  end_date: string
  income: string
  expense: string
  savings: string
  savings_rate_percent: string
}

export interface CategorySpend {
  category_id: string | null
  category_name: string
  total: string
  percentage: string
}

export interface TrendPoint {
  month: string
  income: string
  expense: string
  savings: string
  savings_rate_percent: string | null
}

export interface UnusualItem {
  kind: 'TRANSACTION' | 'CATEGORY'
  category_id: string | null
  category_name: string
  transaction_id: string | null
  amount: string
  threshold: string
  expected_amount: string | null
  deviation_percent: string | null
  detected_at: string | null
  message: string
}
export type AlertType = 'BUDGET_WARNING' | 'BUDGET_EXCEEDED' | 'UNUSUAL_SPENDING' | 'RECURRING_DUE'

export interface Alert {
  id: string
  alert_type: AlertType
  message: string
  is_read: boolean
  created_at: string
}

export interface UserUpdateInput {
  full_name?: string
  currency?: string
  current_password?: string
  new_password?: string
}

export type RecurringFrequency = 'WEEKLY' | 'BIWEEKLY' | 'MONTHLY'
export type RecurringStatus = 'DETECTED' | 'CONFIRMED' | 'DISMISSED'

export interface RecurringExpense {
  id: string
  account_id: string
  category_id: string | null
  merchant: string
  avg_amount: string
  frequency: RecurringFrequency
  next_due_date: string
  status: RecurringStatus
}

export interface RecurringList {
  items: RecurringExpense[]
  total_monthly_cost: string
}

export interface DetectionResult {
  detected: number
  items: RecurringExpense[]
}


export type GoalStatus = 'ACTIVE' | 'COMPLETED'

export interface Goal {
  id: string
  name: string
  target_amount: string
  saved_amount: string
  target_date: string
  status: GoalStatus
  progress_percent: string
  remaining_amount: string
  required_monthly_saving: string
}

export interface GoalInput {
  name: string
  target_amount: string
  target_date: string
}

export interface GoalPatch extends Partial<GoalInput> {
  status?: GoalStatus
}

export interface MonthlyReport {
  month: string
  income: string
  expense: string
  savings: string
  categories: CategorySpend[]
  budgets: Budget[]
  recurring: RecurringExpense[]
  recurring_monthly_cost: string
}