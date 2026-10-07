export const MAX_UPLOAD_MB = 5

export function validateCsvFile(file: File): string | null {
  if (!file.name.toLowerCase().endsWith('.csv')) return 'Only .csv files are accepted'
  if (file.size === 0) return 'The selected file is empty'
  if (file.size > MAX_UPLOAD_MB * 1024 * 1024) return `File exceeds the ${MAX_UPLOAD_MB} MB limit`
  return null
}