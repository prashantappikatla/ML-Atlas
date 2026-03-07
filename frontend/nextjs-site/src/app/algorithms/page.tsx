import { getAllAlgorithms } from '@/lib/mdx'

export const metadata = { title: 'Algorithms' }

export default function AlgorithmsPage() {
  const algorithms = getAllAlgorithms()

  return (
    <div className="mx-auto max-w-7xl p-8">
      <h1 className="text-3xl font-bold">All Algorithms</h1>
      <p className="mt-2 text-gray-600">{algorithms.length} algorithms documented</p>
      {/* AlgorithmGrid component will go here */}
    </div>
  )
}
