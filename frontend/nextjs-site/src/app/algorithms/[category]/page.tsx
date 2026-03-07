import { getAlgorithmsByCategory } from '@/lib/mdx'
import { toTitleCase } from '@/lib/utils'

interface Props {
  params: Promise<{ category: string }>
}

export async function generateMetadata({ params }: Props) {
  const { category } = await params
  return { title: toTitleCase(category) }
}

export default async function CategoryPage({ params }: Props) {
  const { category } = await params
  const algorithms = getAlgorithmsByCategory(category)

  return (
    <div className="mx-auto max-w-7xl p-8">
      <h1 className="text-3xl font-bold">{toTitleCase(category)}</h1>
      <p className="mt-2 text-gray-600">{algorithms.length} algorithms</p>
      {/* AlgorithmGrid component will go here */}
    </div>
  )
}
