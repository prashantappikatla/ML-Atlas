import { api } from '@/lib/api-client'
import { LabCard } from '@/components/lab/LabCard'
import { FlaskConical } from 'lucide-react'

export const revalidate = 3600
export const metadata = { title: 'Labs' }

async function getLabs() {
  try {
    const data = (await api.labs.list()) as any
    if (Array.isArray(data)) return data
    if (data?.data) return data.data
    return []
  } catch {
    return []
  }
}

export default async function LabsPage() {
  const labs = await getLabs()

  return (
    <div className="mx-auto max-w-7xl px-4 py-10 sm:px-6 lg:px-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-slate-900">Interactive Labs</h1>
        <p className="mt-2 text-slate-500">
          Hands-on Streamlit and Gradio experiments for machine learning algorithms. Explore
          parameters, visualize results, and experiment with real data.
        </p>
      </div>

      {labs.length > 0 ? (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {labs.map((lab: any) => (
            <LabCard
              key={lab.id}
              lab={lab}
              algorithmSlug={lab.algorithm_slug}
              algorithmCategory={lab.algorithm_category}
              algorithmName={lab.algorithm_name}
            />
          ))}
        </div>
      ) : (
        <div className="flex min-h-64 flex-col items-center justify-center rounded-xl border border-dashed border-slate-200 bg-slate-50 text-center">
          <FlaskConical className="h-12 w-12 text-slate-200" />
          <p className="mt-3 font-medium text-slate-400">No labs available yet</p>
          <p className="mt-1 text-sm text-slate-300">
            Labs will appear here as algorithms are implemented. Coming in Phase 3.
          </p>
        </div>
      )}
    </div>
  )
}
