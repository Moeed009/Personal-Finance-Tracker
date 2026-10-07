import { useEffect, useRef, useState } from 'react'
import { X } from 'lucide-react'
import { Button } from '@/components/Button'
import { SelectField } from '@/components/SelectField'
import { TextField } from '@/components/TextField'
import { hasActiveFilters, type FilterPatch, type TransactionFilters } from '@/lib/transaction-filters'
import type { Account, Category } from '@/types/api'

interface TransactionFilterBarProps {
  filters: TransactionFilters
  accounts: Account[]
  categories: Category[]
  onChange: (patch: FilterPatch) => void
  onClear: () => void
}

export function TransactionFilterBar({ filters, accounts, categories, onChange, onClear }: TransactionFilterBarProps) {
  const [searchText, setSearchText] = useState(filters.search)
  const timer = useRef<number | undefined>(undefined)

  useEffect(() => () => window.clearTimeout(timer.current), [])

  const handleSearch = (value: string) => {
    setSearchText(value)
    window.clearTimeout(timer.current)
    timer.current = window.setTimeout(() => onChange({ search: value.trim() }), 400)
  }

  const handleClear = () => {
    window.clearTimeout(timer.current)
    setSearchText('')
    onClear()
  }

  return (
    <div className="mb-4 rounded-xl bg-white p-4 shadow-sm ring-1 ring-slate-200">
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <div className="sm:col-span-2">
          <TextField
            label="Search"
            placeholder="Description or merchant"
            value={searchText}
            onChange={(event) => handleSearch(event.target.value)}
          />
        </div>

        <SelectField label="Type" value={filters.type} onChange={(event) => onChange({ type: event.target.value })}>
          <option value="">All types</option>
          <option value="INCOME">Income</option>
          <option value="EXPENSE">Expense</option>
        </SelectField>

        <SelectField
          label="Account"
          value={filters.account_id}
          onChange={(event) => onChange({ account_id: event.target.value })}
        >
          <option value="">All accounts</option>
          {accounts.map((account) => (
            <option key={account.id} value={account.id}>
              {account.name}
            </option>
          ))}
        </SelectField>

        <SelectField
          label="Category"
          value={filters.category_id}
          onChange={(event) => onChange({ category_id: event.target.value })}
        >
          <option value="">All categories</option>
          {categories.map((category) => (
            <option key={category.id} value={category.id}>
              {category.name}
            </option>
          ))}
        </SelectField>

        <TextField
          label="From"
          type="date"
          value={filters.date_from}
          onChange={(event) => onChange({ date_from: event.target.value })}
        />
        <TextField
          label="To"
          type="date"
          value={filters.date_to}
          onChange={(event) => onChange({ date_to: event.target.value })}
        />
      </div>

      {hasActiveFilters(filters) && (
        <div className="mt-3 flex justify-end">
          <Button variant="secondary" onClick={handleClear}>
            <X size={16} />
            Clear filters
          </Button>
        </div>
      )}
    </div>
  )
}