import { notFound } from 'next/navigation'
import { getAlgorithmBySlug, getAllAlgorithmSlugs } from '@/lib/mdx'

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
  return { title: page.frontmatter.title }
}

export default async function AlgorithmPage({ params }: Props) {
  const { category, slug } = await params
  const page = getAlgorithmBySlug(category, slug)
  if (!page) notFound()

  return (
    <article className="mx-auto max-w-4xl p-8">
      <h1 className="text-4xl font-bold">{page.frontmatter.title}</h1>
      <div className="mt-2 flex gap-2 text-sm text-gray-500">
        <span>{page.frontmatter.year}</span>
        <span>·</span>
        <span>{page.frontmatter.author}</span>
        <span>·</span>
        <span>{page.readingTimeMinutes} min read</span>
      </div>
      {/* MDXContent component will render page.content here */}
      <div className="prose mt-8 max-w-none">
        <pre className="text-xs text-gray-400">{page.content.slice(0, 200)}…</pre>
      </div>
    </article>
  )
}
