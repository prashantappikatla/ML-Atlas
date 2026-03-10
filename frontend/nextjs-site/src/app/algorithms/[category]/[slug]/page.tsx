import { notFound } from 'next/navigation'
import Link from 'next/link'
import { Clock, FlaskConical } from 'lucide-react'
import { getAlgorithmBySlug, getAllAlgorithmSlugs } from '@/lib/mdx'
import { getCategoryMeta } from '@/lib/categories'
import { extractHeadings } from '@/lib/toc'
import { Breadcrumbs } from '@/components/algorithm/Breadcrumbs'
import { StatusBadge } from '@/components/algorithm/StatusBadge'
import { ComplexityBadge } from '@/components/algorithm/ComplexityBadge'
import { AlgorithmMeta } from '@/components/algorithm/AlgorithmMeta'
import { RelatedAlgorithms } from '@/components/algorithm/RelatedAlgorithms'
import { TableOfContents } from '@/components/mdx/TableOfContents'
import { MDXContent } from '@/components/mdx/MDXContent'

interface Props {
  params: Promise<{ category: string; slug: string }>
}

export async function generateStaticParams() {
  return getAllAlgorithmSlugs()
}

export async function generateMetadata({ params }: Props) {
  const { category, slug } = await params
  const page = getAlgorithmBySlug(category, slug)
  if (!page) return {}
  return {
    title: page.frontmatter.title,
    description: `${page.frontmatter.title} — ${page.frontmatter.paper || 'ML algorithm documentation, implementation, and interactive lab.'}`,
  }
}

export default async function AlgorithmPage({ params }: Props) {
  const { category, slug } = await params
  const page = getAlgorithmBySlug(category, slug)
  if (!page) notFound()

  const { frontmatter, content, readingTimeMinutes } = page
  const categoryMeta = getCategoryMeta(category)
  const headings = extractHeadings(content)

  const breadcrumbItems = [
    { label: 'Algorithms', href: '/algorithms' },
    { label: categoryMeta?.name ?? category, href: `/algorithms/${category}` },
    { label: frontmatter.title },
  ]

  return (
    <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
      <Breadcrumbs items={breadcrumbItems} />

      <div className="mt-6 lg:grid lg:grid-cols-[1fr_280px] lg:gap-10">
        {/* Main content */}
        <div className="min-w-0">
          <header className="mb-8 border-b border-slate-200 pb-6">
            <div className="flex flex-wrap items-center gap-2">
              <StatusBadge status={frontmatter.status} />
              <ComplexityBadge complexity={frontmatter.complexity} />
              {categoryMeta && (
                <Link
                  href={`/algorithms/${category}`}
                  className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${categoryMeta.bgColor} ${categoryMeta.textColor}`}
                >
                  {categoryMeta.name}
                </Link>
              )}
            </div>

            <h1 className="mt-3 text-4xl font-bold tracking-tight text-slate-900">
              {frontmatter.title}
            </h1>

            <div className="mt-3 flex flex-wrap items-center gap-3 text-sm text-slate-500">
              {frontmatter.year && <span>{frontmatter.year}</span>}
              {frontmatter.year && frontmatter.author && <span>·</span>}
              {frontmatter.author && <span>{frontmatter.author}</span>}
              <span>·</span>
              <span className="flex items-center gap-1">
                <Clock className="h-3.5 w-3.5" />
                {readingTimeMinutes} min read
              </span>
              {frontmatter.lab_url && (
                <>
                  <span>·</span>
                  <a
                    href={frontmatter.lab_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center gap-1 text-indigo-600 hover:text-indigo-800"
                  >
                    <FlaskConical className="h-3.5 w-3.5" />
                    Open Lab
                  </a>
                </>
              )}
            </div>

            {frontmatter.tags && frontmatter.tags.length > 0 && (
              <div className="mt-3 flex flex-wrap gap-1.5">
                {frontmatter.tags.map((tag) => (
                  <span
                    key={tag}
                    className="rounded-md bg-slate-100 px-2 py-0.5 text-xs text-slate-600"
                  >
                    {tag}
                  </span>
                ))}
              </div>
            )}
          </header>

          <article className="prose prose-slate max-w-none prose-headings:scroll-mt-20 prose-a:text-indigo-600 prose-code:font-mono prose-pre:bg-slate-950 prose-pre:text-slate-100">
            <MDXContent source={content} />
          </article>
        </div>

        {/* Right sidebar */}
        <aside className="hidden lg:block">
          <div className="sticky top-20 space-y-4">
            {headings.length > 0 && <TableOfContents headings={headings} />}
            <AlgorithmMeta frontmatter={frontmatter} />
            {frontmatter.related && frontmatter.related.length > 0 && (
              <RelatedAlgorithms slugs={frontmatter.related} currentCategory={category} />
            )}
          </div>
        </aside>
      </div>
    </div>
  )
}
