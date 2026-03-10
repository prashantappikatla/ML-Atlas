import { api } from '@/lib/api-client'
import { AlgorithmBrowser } from '@/components/filters/AlgorithmBrowser'
import { Algorithm, AlgorithmListResponse } from '@/types/algorithm'

export const dynamic = 'force-dynamic'
export const metadata = { title: 'Algorithms' }

async function getAlgorithms(): Promise<Algorithm[]> {
  try {
    const data = (await api.algorithms.list()) as AlgorithmListResponse | Algorithm[]
    if (Array.isArray(data)) return data
    if ('data' in data) return (data as AlgorithmListResponse).data
    return []
  } catch {
    return []
  }
}

export default async function AlgorithmsPage() {
  const algorithms = await getAlgorithms()

  return (
    <div className="mx-auto max-w-7xl px-4 py-10 sm:px-6 lg:px-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-slate-900">All Algorithms</h1>
        <p className="mt-2 text-slate-500">
          Browse and filter {algorithms.length > 0 ? algorithms.length : 278} ML algorithms across
          10 major categories.
        </p>
      </div>
      <AlgorithmBrowser algorithms={algorithms} />
    </div>
  )
}
