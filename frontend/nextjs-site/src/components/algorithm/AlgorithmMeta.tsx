import Link from 'next/link'
import { Calendar, User, FileText, Tag } from 'lucide-react'
import { AlgorithmFrontmatter } from '@/types/mdx'
import { getCategoryMeta } from '@/lib/categories'

interface AlgorithmMetaProps {
  frontmatter: AlgorithmFrontmatter
}

export function AlgorithmMeta({ frontmatter }: AlgorithmMetaProps) {
  const category = getCategoryMeta(frontmatter.category)

  return (
    <div className="rounded-lg border border-slate-200 bg-white p-4">
      <h3 className="mb-3 text-xs font-semibold uppercase tracking-wider text-slate-400">
        Metadata
      </h3>
      <dl className="space-y-2.5">
        {frontmatter.year && (
          <div className="flex items-start gap-2">
            <Calendar className="mt-0.5 h-4 w-4 shrink-0 text-slate-400" />
            <div>
              <dt className="text-xs text-slate-400">Year</dt>
              <dd className="text-sm font-medium text-slate-700">{frontmatter.year}</dd>
            </div>
          </div>
        )}
        {frontmatter.author && (
          <div className="flex items-start gap-2">
            <User className="mt-0.5 h-4 w-4 shrink-0 text-slate-400" />
            <div>
              <dt className="text-xs text-slate-400">Author</dt>
              <dd className="text-sm font-medium text-slate-700">{frontmatter.author}</dd>
            </div>
          </div>
        )}
        {frontmatter.paper && (
          <div className="flex items-start gap-2">
            <FileText className="mt-0.5 h-4 w-4 shrink-0 text-slate-400" />
            <div>
              <dt className="text-xs text-slate-400">Paper</dt>
              <dd className="text-sm text-slate-700">{frontmatter.paper}</dd>
            </div>
          </div>
        )}
        {category && (
          <div className="flex items-start gap-2">
            <Tag className="mt-0.5 h-4 w-4 shrink-0 text-slate-400" />
            <div>
              <dt className="text-xs text-slate-400">Category</dt>
              <dd>
                <Link
                  href={`/algorithms/${frontmatter.category}`}
                  className={`text-sm font-medium ${category.textColor} hover:underline`}
                >
                  {category.name}
                </Link>
              </dd>
            </div>
          </div>
        )}
      </dl>
    </div>
  )
}
