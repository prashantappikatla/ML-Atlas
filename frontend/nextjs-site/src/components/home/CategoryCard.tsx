import Link from 'next/link'
import { ArrowRight } from 'lucide-react'
import { CategoryMeta } from '@/lib/categories'

interface CategoryCardProps {
  category: CategoryMeta
  documented?: number
  total?: number
}

export function CategoryCard({ category, documented = 0, total }: CategoryCardProps) {
  const count = total ?? category.count
  const progress = count > 0 ? Math.round((documented / count) * 100) : 0

  return (
    <Link
      href={`/algorithms/${category.slug}`}
      className="group relative flex flex-col overflow-hidden rounded-xl border border-slate-200 bg-white p-5 transition-all hover:border-slate-300 hover:shadow-md"
    >
      {/* Color accent bar */}
      <div
        className="absolute inset-x-0 top-0 h-1 rounded-t-xl"
        style={{ backgroundColor: category.color }}
      />

      <div className="mt-1">
        <span
          className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${category.bgColor} ${category.textColor}`}
        >
          {count} algorithms
        </span>
      </div>

      <h3 className="mt-3 font-semibold text-slate-900 group-hover:text-indigo-600">
        {category.name}
      </h3>
      <p className="mt-1 flex-1 text-sm text-slate-500 line-clamp-2">{category.description}</p>

      {/* Progress bar */}
      <div className="mt-4">
        <div className="flex items-center justify-between text-xs text-slate-400 mb-1">
          <span>{documented} documented</span>
          <span>{progress}%</span>
        </div>
        <div className="h-1.5 overflow-hidden rounded-full bg-slate-100">
          <div
            className="h-full rounded-full transition-all"
            style={{ width: `${progress}%`, backgroundColor: category.color }}
          />
        </div>
      </div>

      <div className="mt-3 flex items-center gap-1 text-xs font-medium text-slate-400 group-hover:text-indigo-600">
        Browse algorithms
        <ArrowRight className="h-3.5 w-3.5" />
      </div>
    </Link>
  )
}
