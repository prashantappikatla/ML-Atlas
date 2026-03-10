import { AlgorithmCard } from './AlgorithmCard'
import { Algorithm } from '@/types/algorithm'
import { AlgorithmFrontmatter } from '@/types/mdx'

type GridItem = Algorithm | AlgorithmFrontmatter

interface AlgorithmGridProps {
  algorithms: GridItem[]
  emptyMessage?: string
}

export function AlgorithmGrid({ algorithms, emptyMessage = 'No algorithms found.' }: AlgorithmGridProps) {
  if (algorithms.length === 0) {
    return (
      <div className="flex min-h-48 items-center justify-center rounded-lg border border-dashed border-slate-200 bg-slate-50">
        <p className="text-sm text-slate-400">{emptyMessage}</p>
      </div>
    )
  }

  return (
    <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
      {algorithms.map((alg) => (
        <AlgorithmCard key={alg.slug} algorithm={alg as any} />
      ))}
    </div>
  )
}
