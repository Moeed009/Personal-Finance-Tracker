export const MAX_UPLOAD_MB = 5

export function isPdfFile(file: File): boolean {
  return file.name.toLowerCase().endsWith('.pdf')
}

export function validateImportFile(file: File): string | null {
  const name = file.name.toLowerCase()
  if (!name.endsWith('.csv') && !name.endsWith('.pdf')) return 'Only .csv and .pdf files are accepted'
  if (file.size === 0) return 'The selected file is empty'
  if (file.size > MAX_UPLOAD_MB * 1024 * 1024) return `File exceeds the ${MAX_UPLOAD_MB} MB limit`
  return null
}