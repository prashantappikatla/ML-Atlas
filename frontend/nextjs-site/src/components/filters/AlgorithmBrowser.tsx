'use client'

import { useState, useMemo } from 'react'
import { FilterSidebar, FilterState } from './FilterSidebar'
import { AlgorithmGrid } from '@/components/algorithm/AlgorithmGrid'
import { Algorithm } from '@/types/algorithm'

interface AlgorithmBrowserProps {
  algorithms: Algorithm[]
}

export function AlgorithmBrowser({ algorithms }: AlgorithmBrowserProps) {
  const [filters, setFilters] = useState<FilterState>({
    categories: [],
    complexity: [],
    status: [],
    compatibility: [],
  })
  const [search, setSearch] = useState('')

  const filtered = useMemo(() => {
    return algorithms.filter((alg) => {
      if (filters.categories.length > 0 && !filters.categories.includes(alg.category)) return false
      if (filters.complexity.length > 0 && !filters.complexity.includes(alg.complexity)) return false
      if (filters.compatibility.length > 0) {
        const compMap: Record<string, boolean> = {
          tabular: alg.compatibility_tabular,
          image: alg.compatibility_image,
          text: alg.compatibility_text,
          timeseries: alg.compatibility_timeseries,
          graph: alg.compatibility_graph,
        }
        if (!filters.compatibility.some((c) => compMap[c])) return false
      }
      if (search.trim()) {
        const q = search.toLowerCase()
        if (
          !alg.name.toLowerCase().includes(q) &&
          !alg.subcategory.toLowerCase().includes(q) &&
          !(alg.author?.toLowerCase().includes(q))
        )
          return false
      }
      return true
    })
  }, [algorithms, filters, search])

  return (
    <div className="flex gap-8">
      {/* Sidebar — hidden on mobile */}
      <div className="hidden md:block">
        <FilterSidebar
          filters={filters}
          onChange={setFilters}
          counts={{ total: algorithms.length, filtered: filtered.length }}
        />
      </div>

      {/* Main */}
      <div className="flex-1 min-w-0">
        <div className="mb-4 flex items-center gap-3">
          <input
            type="search"
            placeholder="Filter by name, author…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="flex-1 rounded-lg border border-slate-200 px-4 py-2 text-sm placeholder-slate-400 focus:border-indigo-400 focus:outline-none focus:ring-2 focus:ring-indigo-100"
          />
          <p className="hidden shrink-0 text-sm text-slate-400 sm:block">
            {filtered.length} algorithms
          </p>
        </div>
        <AlgorithmGrid algorithms={filtered as any} />
      </div>
    </div>
  )
}
