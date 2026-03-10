import Link from 'next/link'
import { ArrowRight, BookOpen, FlaskConical, Search } from 'lucide-react'
import { CATEGORIES } from '@/lib/categories'
import { CategoryCard } from '@/components/home/CategoryCard'
import { StatsBar } from '@/components/home/StatsBar'
import { api } from '@/lib/api-client'

async function getStats() {
  try {
    const statusData = (await api.status.list()) as { summary?: Record<string, number> } | null
    const summary = statusData?.summary ?? {}
    return {
      total: summary['total'] ?? 278,
      documented: (summary['documented'] ?? 0) + (summary['implemented'] ?? 0) + (summary['lab-ready'] ?? 0),
      implemented: summary['implemented'] ?? 0,
      labReady: summary['lab-ready'] ?? 0,
    }
  } catch {
    return { total: 278, documented: 0, implemented: 0, labReady: 0 }
  }
}

async function getCategoryStats() {
  try {
    const data = (await api.categories.list()) as unknown
    if (Array.isArray(data)) return data as Array<{ slug: string; documented?: number }>
    if (data && typeof data === 'object' && 'data' in data && Array.isArray((data as { data: unknown }).data)) {
      return (data as { data: Array<{ slug: string; documented?: number }> }).data
    }
    return []
  } catch {
    return []
  }
}

export const dynamic = 'force-dynamic'

export default async function HomePage() {
  const [stats, categoryStats] = await Promise.all([getStats(), getCategoryStats()])

  const statItems = [
    { label: 'Total Algorithms', value: stats.total, description: 'across 10 categories' },
    { label: 'Documented', value: stats.documented, description: 'fully written up' },
    { label: 'Implemented', value: stats.implemented, description: 'with code' },
    { label: 'Labs Ready', value: stats.labReady, description: 'interactive demos' },
  ]

  const categoryDocMap: Record<string, number> = (categoryStats ?? []).reduce(
    (acc: Record<string, number>, cs: { slug: string; documented?: number }) => {
      if (cs.slug) acc[cs.slug] = cs.documented ?? 0
      return acc
    },
    {}
  )

  return (
    <div>
      {/* Hero */}
      <section className="border-b border-slate-200 bg-gradient-to-b from-slate-50 to-white">
        <div className="mx-auto max-w-7xl px-4 py-20 sm:px-6 lg:px-8 lg:py-28">
          <div className="mx-auto max-w-3xl text-center">
            <span className="inline-flex items-center rounded-full bg-indigo-50 px-3 py-1 text-sm font-medium text-indigo-700 ring-1 ring-inset ring-indigo-200">
              278 ML Algorithms
            </span>
            <h1 className="mt-4 text-5xl font-bold tracking-tight text-slate-900 sm:text-6xl">
              Machine Learning
              <br />
              <span className="text-indigo-600">Atlas</span>
            </h1>
            <p className="mt-6 text-xl text-slate-600">
              A comprehensive reference for machine learning algorithms — theory, math, code, and
              interactive labs. Built for deep understanding.
            </p>
            <div className="mt-8 flex flex-col items-center gap-3 sm:flex-row sm:justify-center">
              <Link
                href="/algorithms"
                className="inline-flex items-center gap-2 rounded-lg bg-indigo-600 px-6 py-3 text-sm font-semibold text-white shadow-sm hover:bg-indigo-700"
              >
                Browse Algorithms
                <ArrowRight className="h-4 w-4" />
              </Link>
              <Link
                href="/search"
                className="inline-flex items-center gap-2 rounded-lg border border-slate-200 bg-white px-6 py-3 text-sm font-semibold text-slate-700 hover:bg-slate-50"
              >
                <Search className="h-4 w-4" />
                Search
              </Link>
            </div>
          </div>
        </div>
      </section>

      <div className="mx-auto max-w-7xl px-4 py-16 sm:px-6 lg:px-8 space-y-16">
        {/* Stats */}
        <StatsBar stats={statItems} />

        {/* Categories */}
        <section>
          <div className="mb-6 flex items-center justify-between">
            <div>
              <h2 className="text-2xl font-bold text-slate-900">Browse by Category</h2>
              <p className="mt-1 text-sm text-slate-500">
                10 major categories covering the full ML landscape
              </p>
            </div>
            <Link
              href="/algorithms"
              className="hidden text-sm font-medium text-indigo-600 hover:text-indigo-800 sm:flex items-center gap-1"
            >
              View all
              <ArrowRight className="h-4 w-4" />
            </Link>
          </div>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5">
            {CATEGORIES.map((cat) => (
              <CategoryCard
                key={cat.slug}
                category={cat}
                documented={categoryDocMap[cat.slug] ?? 0}
                total={cat.count}
              />
            ))}
          </div>
        </section>

        {/* How it works */}
        <section className="rounded-2xl border border-slate-200 bg-slate-50 p-8">
          <h2 className="mb-8 text-center text-2xl font-bold text-slate-900">
            How ML Atlas Works
          </h2>
          <div className="grid gap-6 sm:grid-cols-3">
            {[
              {
                icon: <Search className="h-6 w-6 text-indigo-600" />,
                title: 'Browse & Search',
                desc: 'Find algorithms by category, data type, complexity, or search by name. Filter 278 algorithms to exactly what you need.',
              },
              {
                icon: <BookOpen className="h-6 w-6 text-indigo-600" />,
                title: 'Learn the Theory',
                desc: 'Every algorithm has structured documentation: overview, history, mathematical intuition, algorithm steps, and parameters.',
              },
              {
                icon: <FlaskConical className="h-6 w-6 text-indigo-600" />,
                title: 'Experiment in Labs',
                desc: 'Interactive Streamlit and Gradio labs let you explore parameters, visualize decision boundaries, and run experiments.',
              },
            ].map(({ icon, title, desc }) => (
              <div key={title} className="flex flex-col items-center text-center">
                <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-white shadow-sm border border-slate-200">
                  {icon}
                </div>
                <h3 className="mt-4 font-semibold text-slate-900">{title}</h3>
                <p className="mt-2 text-sm text-slate-500">{desc}</p>
              </div>
            ))}
          </div>
        </section>
      </div>
    </div>
  )
}
