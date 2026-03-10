import Link from 'next/link'
import { ExternalLink, FlaskConical } from 'lucide-react'
import { getCategoryMeta } from '@/lib/categories'

interface LabCardProps {
  lab: {
    id: number
    algorithm_id: number
    lab_name: string
    lab_type: string
    url?: string
    framework: string
  }
  algorithmSlug?: string
  algorithmCategory?: string
  algorithmName?: string
}

export function LabCard({ lab, algorithmSlug, algorithmCategory, algorithmName }: LabCardProps) {
  const category = algorithmCategory ? getCategoryMeta(algorithmCategory) : undefined

  return (
    <div className="flex flex-col rounded-xl border border-slate-200 bg-white p-5 hover:border-indigo-300 hover:shadow-sm transition-all">
      <div className="flex items-start justify-between gap-2">
        <div className="flex items-center gap-2">
          <FlaskConical className="h-5 w-5 text-indigo-500 shrink-0" />
          <h3 className="font-semibold text-slate-900">{lab.lab_name}</h3>
        </div>
        <span className="shrink-0 rounded-full bg-slate-100 px-2 py-0.5 text-xs font-medium text-slate-500 capitalize">
          {lab.framework}
        </span>
      </div>

      {algorithmName && (
        <p className="mt-1 text-sm text-slate-500">
          {category && (
            <span className={`mr-1 text-xs font-medium ${category.textColor}`}>
              {category.name}
            </span>
          )}
          {algorithmName}
        </p>
      )}

      <span className="mt-2 inline-flex w-fit items-center rounded-md bg-indigo-50 px-2 py-0.5 text-xs font-medium text-indigo-700 capitalize">
        {lab.lab_type.replace('-', ' ')}
      </span>

      <div className="mt-4 flex gap-2">
        {algorithmSlug && algorithmCategory && (
          <Link
            href={`/algorithms/${algorithmCategory}/${algorithmSlug}`}
            className="flex-1 rounded-lg border border-slate-200 px-3 py-2 text-center text-sm font-medium text-slate-600 hover:bg-slate-50"
          >
            View Algorithm
          </Link>
        )}
        {lab.url ? (
          <a
            href={lab.url}
            target="_blank"
            rel="noopener noreferrer"
            className="flex flex-1 items-center justify-center gap-1.5 rounded-lg bg-indigo-600 px-3 py-2 text-sm font-medium text-white hover:bg-indigo-700"
          >
            Open Lab
            <ExternalLink className="h-3.5 w-3.5" />
          </a>
        ) : (
          <span className="flex flex-1 items-center justify-center gap-1.5 rounded-lg bg-slate-100 px-3 py-2 text-sm font-medium text-slate-400 cursor-not-allowed">
            Coming Soon
          </span>
        )}
      </div>
    </div>
  )
}
