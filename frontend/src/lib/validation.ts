import { z } from 'zod'

export const positiveAmount = z
  .string()
  .trim()
  .regex(/^\d{1,10}(\.\d{1,2})?$/, 'Enter a valid amount (up to 2 decimals)')
  .refine((value) => Number(value) > 0, 'Amount must be greater than 0')

export const isoDate = z.string().regex(/^\d{4}-\d{2}-\d{2}$/, 'Select a date')