import { AlgorithmCard } from './AlgorithmCard'
import { Algorithm } from '@/types/algorithm'
import { AlgorithmFrontmatter } from '@/types/mdx'

interface SubcategorySectionProps {
  subcategory: string
  algorithms: (Algorithm | AlgorithmFrontmatter)[]
}

export function SubcategorySection({ subcategory, algorithms }: SubcategorySectionProps) {
  return (
    <div>
      <div className="mb-3 flex items-center gap-3">
        <h2 className="text-lg font-semibold capitalize text-slate-800">{subcategory}</h2>
        <span className="rounded-full bg-slate-100 px-2.5 py-0.5 text-xs font-medium text-slate-500">
          {algorithms.length}
        </span>
      </div>
      <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
        {algorithms.map((alg) => (
          <AlgorithmCard key={alg.slug} algorithm={alg as any} />
        ))}
      </div>
    </div>
  )
}
