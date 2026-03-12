import Link from 'next/link'
import { ArrowRight } from 'lucide-react'
import { getAllAlgorithmSlugs } from '@/lib/mdx'

interface RelatedAlgorithmsProps {
  slugs: string[]
  currentCategory: string
}

export function RelatedAlgorithms({ slugs, currentCategory }: RelatedAlgorithmsProps) {
  if (!slugs || slugs.length === 0) return null

  const allSlugs = getAllAlgorithmSlugs()

  // Only render slugs that have a corresponding MDX file — prevents 404 links
  const validSlugs = slugs.filter((slug) => allSlugs.some((s) => s.slug === slug))

  const related = validSlugs.slice(0, 5).map((slug) => {
    const found = allSlugs.find((s) => s.slug === slug)
    return {
      slug,
      category: found?.category ?? currentCategory,
      label: slug
        .split('-')
        .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
        .join(' '),
    }
  })

  return (
    <div className="rounded-lg border border-slate-200 bg-white p-4">
      <h3 className="mb-3 text-xs font-semibold uppercase tracking-wider text-slate-400">
        Related Algorithms
      </h3>
      <ul className="space-y-1">
        {related.map(({ slug, category, label }) => (
          <li key={slug}>
            <Link
              href={`/algorithms/${category}/${slug}`}
              className="flex items-center justify-between rounded px-2 py-1.5 text-sm text-slate-600 hover:bg-slate-50 hover:text-indigo-600"
            >
              <span>{label}</span>
              <ArrowRight className="h-3.5 w-3.5 text-slate-300" />
            </Link>
          </li>
        ))}
      </ul>
    </div>
  )
}
