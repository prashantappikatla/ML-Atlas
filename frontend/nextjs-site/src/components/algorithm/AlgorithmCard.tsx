import Link from 'next/link'
import { Algorithm } from '@/types/algorithm'
import { AlgorithmFrontmatter } from '@/types/mdx'
import { StatusBadge } from './StatusBadge'
import { ComplexityBadge } from './ComplexityBadge'
import { getCategoryMeta } from '@/lib/categories'

// Accepts either DB Algorithm or MDX frontmatter
type CardData =
  | (Pick<Algorithm, 'name' | 'slug' | 'category' | 'subcategory' | 'year' | 'author' | 'complexity'> & {
      status?: string
      tags?: never
    })
  | AlgorithmFrontmatter

interface AlgorithmCardProps {
  algorithm: CardData
  href?: string
}

function getDisplayName(algorithm: CardData): string {
  if ('title' in algorithm) return algorithm.title
  return (algorithm as any).name ?? ''
}

export function AlgorithmCard({ algorithm, href }: AlgorithmCardProps) {
  const category = getCategoryMeta(algorithm.category)
  const targetHref =
    href ?? `/algorithms/${algorithm.category}/${algorithm.slug}`

  const status = 'status' in algorithm ? algorithm.status : undefined
  const tags = 'tags' in algorithm ? algorithm.tags : undefined
  const displayName = getDisplayName(algorithm)

  return (
    <Link
      href={targetHref}
      className="group flex flex-col rounded-lg border border-slate-200 bg-white p-4 transition-all hover:border-indigo-300 hover:shadow-sm"
    >
      <div className="flex items-start justify-between gap-2">
        <div className="flex-1 min-w-0">
          <p className="text-xs text-slate-400">
            {category?.name ?? algorithm.category}{' '}
            {algorithm.subcategory && `· ${algorithm.subcategory}`}
          </p>
          <h3 className="mt-0.5 truncate font-semibold text-slate-900 group-hover:text-indigo-600">
            {displayName}
          </h3>
        </div>
        <ComplexityBadge complexity={algorithm.complexity} />
      </div>

      {algorithm.year || algorithm.author ? (
        <p className="mt-1.5 text-xs text-slate-400">
          {algorithm.year}
          {algorithm.year && algorithm.author && ' · '}
          {algorithm.author}
        </p>
      ) : null}

      {tags && tags.length > 0 && (
        <div className="mt-2 flex flex-wrap gap-1">
          {tags.slice(0, 3).map((tag) => (
            <span
              key={tag}
              className="rounded bg-slate-100 px-1.5 py-0.5 text-xs text-slate-500"
            >
              {tag}
            </span>
          ))}
        </div>
      )}

      {status && (
        <div className="mt-3 pt-3 border-t border-slate-100">
          <StatusBadge status={status as any} />
        </div>
      )}
    </Link>
  )
}
