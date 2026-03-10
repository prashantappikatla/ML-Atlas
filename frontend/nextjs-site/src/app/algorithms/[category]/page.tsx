import { notFound } from 'next/navigation'
import { api } from '@/lib/api-client'
import { getCategoryMeta, CATEGORIES } from '@/lib/categories'
import { Breadcrumbs } from '@/components/algorithm/Breadcrumbs'
import { SubcategorySection } from '@/components/algorithm/SubcategorySection'
import { Algorithm } from '@/types/algorithm'

interface Props {
  params: Promise<{ category: string }>
}

export async function generateStaticParams() {
  return CATEGORIES.map((c) => ({ category: c.slug }))
}

export async function generateMetadata({ params }: Props) {
  const { category } = await params
  const meta = getCategoryMeta(category)
  return { title: meta?.name ?? category }
}

async function getCategoryAlgorithms(slug: string): Promise<Algorithm[]> {
  try {
    const data = (await api.algorithms.list({ category: slug })) as any
    if (Array.isArray(data)) return data
    if (data?.data) return data.data
    return []
  } catch {
    return []
  }
}

export default async function CategoryPage({ params }: Props) {
  const { category } = await params
  const categoryMeta = getCategoryMeta(category)
  if (!categoryMeta) notFound()

  const algorithms = await getCategoryAlgorithms(category)

  const bySubcategory = algorithms.reduce<Record<string, Algorithm[]>>((acc, alg) => {
    const sub = alg.subcategory || 'Other'
    if (!acc[sub]) acc[sub] = []
    acc[sub].push(alg)
    return acc
  }, {})

  const subcategories = Object.keys(bySubcategory).sort()
  const documented = algorithms.filter(
    (a) => (a as any).status && (a as any).status !== 'planned'
  ).length

  return (
    <div className="mx-auto max-w-7xl px-4 py-10 sm:px-6 lg:px-8">
      <Breadcrumbs
        items={[{ label: 'Algorithms', href: '/algorithms' }, { label: categoryMeta.name }]}
      />

      <div className="mt-6 border-b border-slate-200 pb-6">
        <span
          className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${categoryMeta.bgColor} ${categoryMeta.textColor}`}
        >
          {algorithms.length || categoryMeta.count} algorithms
        </span>
        <h1 className="mt-2 text-3xl font-bold text-slate-900">{categoryMeta.name}</h1>
        <p className="mt-1 text-slate-500">{categoryMeta.description}</p>

        {algorithms.length > 0 && (
          <div className="mt-4 max-w-sm">
            <div className="mb-1 flex items-center justify-between text-xs text-slate-400">
              <span>{documented} documented</span>
              <span>{Math.round((documented / algorithms.length) * 100)}%</span>
            </div>
            <div className="h-1.5 overflow-hidden rounded-full bg-slate-100">
              <div
                className="h-full rounded-full"
                style={{
                  width: `${Math.round((documented / algorithms.length) * 100)}%`,
                  backgroundColor: categoryMeta.color,
                }}
              />
            </div>
          </div>
        )}
      </div>

      <div className="mt-8 space-y-10">
        {subcategories.length > 0 ? (
          subcategories.map((sub) => (
            <SubcategorySection key={sub} subcategory={sub} algorithms={bySubcategory[sub]} />
          ))
        ) : (
          <div className="flex min-h-48 items-center justify-center rounded-lg border border-dashed border-slate-200 bg-slate-50">
            <div className="text-center">
              <p className="text-slate-400">No algorithms loaded from backend yet.</p>
              <p className="mt-1 text-xs text-slate-300">
                Start the FastAPI backend to see all {categoryMeta.count} algorithms.
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
