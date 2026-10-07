import { FREQUENCY_LABELS } from '@/lib/recurring'
import type { MonthlyReport } from '@/types/api'

const FORMULA_START = /^[=+\-@\t\r]/

function text(value: string): string {
  const safe = FORMULA_START.test(value) ? `'${value}` : value
  return /[",\n\r]/.test(safe) ? `"${safe.replace(/"/g, '""')}"` : safe
}

function line(cells: string[]): string {
  return cells.join(',')
}

export function reportToCsv(report: MonthlyReport): string {
  const lines: string[] = [
    line([text('Monthly report'), text(report.month.slice(0, 7))]),
    line([text('Income'), report.income]),
    line([text('Expenses'), report.expense]),
    line([text('Savings'), report.savings]),
    '',
    line([text('Category'), text('Amount'), text('Percentage')]),
    ...report.categories.map((item) => line([text(item.category_name), item.total, item.percentage])),
    '',
    line([text('Budget category'), text('Limit'), text('Spent'), text('Remaining'), text('Percent used'), text('Status')]),
    ...report.budgets.map((budget) =>
      line([
        text(budget.category_name),
        budget.limit_amount,
        budget.spent,
        budget.remaining,
        budget.percent_used,
        text(budget.status),
      ]),
    ),
    '',
    line([text('Recurring payment'), text('Frequency'), text('Average amount'), text('Next due date'), text('Status')]),
    ...report.recurring.map((item) =>
      line([
        text(item.merchant),
        text(FREQUENCY_LABELS[item.frequency]),
        item.avg_amount,
        item.next_due_date,
        text(item.status),
      ]),
    ),
    line([text('Estimated monthly recurring cost'), report.recurring_monthly_cost]),
  ]

  return `\uFEFF${lines.join('\r\n')}`
}