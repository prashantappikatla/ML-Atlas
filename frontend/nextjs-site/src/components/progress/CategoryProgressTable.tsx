import Link from 'next/link'
import { CATEGORIES } from '@/lib/categories'
import { ProgressBar } from './ProgressBar'

interface CategoryStatus {
  slug: string
  planned: number
  in_progress: number
  documented: number
  implemented: number
  lab_ready: number
  total: number
}

interface CategoryProgressTableProps {
  byCategory: CategoryStatus[]
}

const STATUS_COLS = [
  { key: 'planned', label: 'Planned', color: '#94a3b8' },
  { key: 'in_progress', label: 'In Progress', color: '#f59e0b' },
  { key: 'documented', label: 'Documented', color: '#3b82f6' },
  { key: 'implemented', label: 'Implemented', color: '#8b5cf6' },
  { key: 'lab_ready', label: 'Lab Ready', color: '#10b981' },
] as const

export function CategoryProgressTable({ byCategory }: CategoryProgressTableProps) {
  return (
    <div className="overflow-hidden rounded-xl border border-slate-200 bg-white">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-slate-200 bg-slate-50">
            <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-slate-500">
              Category
            </th>
            <th className="px-4 py-3 text-right text-xs font-semibold uppercase tracking-wider text-slate-500">
              Total
            </th>
            {STATUS_COLS.map(({ key, label }) => (
              <th
                key={key}
                className="hidden px-4 py-3 text-right text-xs font-semibold uppercase tracking-wider text-slate-500 lg:table-cell"
              >
                {label}
              </th>
            ))}
            <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-slate-500">
              Progress
            </th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100">
          {byCategory.map((row, i) => {
            const catMeta = CATEGORIES.find((c) => c.slug === row.slug)
            const documented = row.documented + row.implemented + row.lab_ready
            return (
              <tr key={row.slug} className={i % 2 === 1 ? 'bg-slate-50/30' : ''}>
                <td className="px-4 py-3">
                  <Link
                    href={`/algorithms/${row.slug}`}
                    className="font-medium text-slate-900 hover:text-indigo-600"
                  >
                    {catMeta?.name ?? row.slug}
                  </Link>
                </td>
                <td className="px-4 py-3 text-right font-medium text-slate-700">{row.total}</td>
                {STATUS_COLS.map(({ key }) => (
                  <td
                    key={key}
                    className="hidden px-4 py-3 text-right text-slate-500 lg:table-cell"
                  >
                    {(row as any)[key] ?? 0}
                  </td>
                ))}
                <td className="px-4 py-3">
                  <div className="flex items-center gap-2">
                    <ProgressBar
                      value={documented}
                      max={row.total}
                      color={catMeta?.color}
                      className="w-24"
                    />
                    <span className="text-xs text-slate-400">
                      {row.total > 0 ? Math.round((documented / row.total) * 100) : 0}%
                    </span>
                  </div>
                </td>
              </tr>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}
