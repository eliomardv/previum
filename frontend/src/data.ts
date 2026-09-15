import type { Company } from './types'
type Reader = <T>(path: string) => Promise<T>
export async function allRecords<T extends Company>(api: Reader, path: string): Promise<T[]> {
  const records: T[] = []
  for (let offset = 0; ; offset += 100) {
    const page = await api<T[]>(path + '?limit=100&offset=' + offset)
    records.push(...page)
    if (page.length < 100) return records
  }
}
