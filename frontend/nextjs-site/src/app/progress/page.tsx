import { api } from '@/lib/api-client'
import { StatusSummary } from '@/components/progress/StatusSummary'
import { CategoryProgressTable } from '@/components/progress/CategoryProgressTable'

export const dynamic = 'force-dynamic'
export const metadata = { title: 'Progress' }

async function getProgressData() {
  try {
    const data = (await api.status.list()) as any
    return data
  } catch {
    return null
  }
}

export default async function ProgressPage() {
  const data = await getProgressData()

  const summary = data?.summary ?? {}
  const byCategory: any[] = data?.by_category ?? []

  const total = summary.total ?? 278
  const planned = summary.planned ?? 0
  const inProgress = summary['in-progress'] ?? 0
  const documented = summary.documented ?? 0
  const implemented = summary.implemented ?? 0
  const labReady = summary['lab-ready'] ?? 0

  return (
    <div className="mx-auto max-w-6xl px-4 py-10 sm:px-6 lg:px-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-slate-900">Implementation Progress</h1>
        <p className="mt-2 text-slate-500">
          Track documentation and lab completion across all 278 algorithms.
        </p>
      </div>

      {data ? (
        <div className="space-y-8">
          <StatusSummary
            total={total}
            planned={planned}
            inProgress={inProgress}
            documented={documented}
            implemented={implemented}
            labReady={labReady}
          />

          {/* Status distribution bar */}
          <div className="rounded-xl border border-slate-200 bg-white p-6">
            <h2 className="mb-4 text-sm font-semibold uppercase tracking-wider text-slate-400">
              Status Distribution
            </h2>
            <div className="flex h-8 overflow-hidden rounded-full">
              {[
                { value: planned, color: '#94a3b8', label: 'Planned' },
                { value: inProgress, color: '#f59e0b', label: 'In Progress' },
                { value: documented, color: '#3b82f6', label: 'Documented' },
                { value: implemented, color: '#8b5cf6', label: 'Implemented' },
                { value: labReady, color: '#10b981', label: 'Lab Ready' },
              ]
                .filter((s) => s.value > 0)
                .map(({ value, color, label }) => (
                  <div
                    key={label}
                    title={`${label}: ${value}`}
                    className="transition-all"
                    style={{ width: `${(value / total) * 100}%`, backgroundColor: color }}
                  />
                ))}
            </div>
            <div className="mt-3 flex flex-wrap gap-4">
              {[
                { value: planned, color: '#94a3b8', label: 'Planned' },
                { value: inProgress, color: '#f59e0b', label: 'In Progress' },
                { value: documented, color: '#3b82f6', label: 'Documented' },
                { value: implemented, color: '#8b5cf6', label: 'Implemented' },
                { value: labReady, color: '#10b981', label: 'Lab Ready' },
              ].map(({ value, color, label }) => (
                <div key={label} className="flex items-center gap-1.5">
                  <div className="h-2.5 w-2.5 rounded-full" style={{ backgroundColor: color }} />
                  <span className="text-xs text-slate-500">
                    {label} ({value})
                  </span>
                </div>
              ))}
            </div>
          </div>

          {byCategory.length > 0 && (
            <div>
              <h2 className="mb-4 text-lg font-semibold text-slate-900">By Category</h2>
              <CategoryProgressTable byCategory={byCategory} />
            </div>
          )}
        </div>
      ) : (
        <div className="flex min-h-64 items-center justify-center rounded-xl border border-dashed border-slate-200 bg-slate-50">
          <div className="text-center">
            <p className="text-slate-400">Could not load progress data.</p>
            <p className="mt-1 text-xs text-slate-300">
              Start the FastAPI backend at localhost:8000 to see live progress.
            </p>
          </div>
        </div>
      )}
    </div>
  )
}
