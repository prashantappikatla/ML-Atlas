'use client'

import { useState, useCallback, useEffect } from 'react'
import { Search, Loader2 } from 'lucide-react'
import { AlgorithmCard } from '@/components/algorithm/AlgorithmCard'
import { Algorithm } from '@/types/algorithm'

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1'

function useDebounce<T>(value: T, delay: number): T {
  const [debounced, setDebounced] = useState(value)
  useEffect(() => {
    const timer = setTimeout(() => setDebounced(value), delay)
    return () => clearTimeout(timer)
  }, [value, delay])
  return debounced
}

export function SearchPage() {
  const [query, setQuery] = useState('')
  const [results, setResults] = useState<Algorithm[]>([])
  const [loading, setLoading] = useState(false)
  const [searched, setSearched] = useState(false)
  const debouncedQuery = useDebounce(query, 300)

  const doSearch = useCallback(async (q: string) => {
    if (!q.trim()) {
      setResults([])
      setSearched(false)
      return
    }
    setLoading(true)
    setSearched(true)
    try {
      const res = await fetch(`${API_BASE}/search?q=${encodeURIComponent(q)}`)
      if (!res.ok) throw new Error('Search failed')
      const data = await res.json()
      const items = Array.isArray(data) ? data : data?.data ?? []
      setResults(items)
    } catch {
      setResults([])
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    doSearch(debouncedQuery)
  }, [debouncedQuery, doSearch])

  return (
    <div>
      {/* Search input */}
      <div className="relative">
        <Search className="absolute left-4 top-1/2 h-5 w-5 -translate-y-1/2 text-slate-400" />
        <input
          type="search"
          placeholder="Search algorithms by name, author, or description…"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          autoFocus
          className="w-full rounded-xl border border-slate-200 bg-white py-4 pl-12 pr-4 text-base shadow-sm placeholder-slate-400 focus:border-indigo-400 focus:outline-none focus:ring-2 focus:ring-indigo-100"
        />
        {loading && (
          <Loader2 className="absolute right-4 top-1/2 h-5 w-5 -translate-y-1/2 animate-spin text-slate-400" />
        )}
      </div>

      {/* Results */}
      <div className="mt-6">
        {!searched && !query && (
          <div className="text-center py-12 text-slate-400">
            <Search className="mx-auto mb-3 h-10 w-10 text-slate-200" />
            <p className="text-sm">Start typing to search across all 278 algorithms</p>
          </div>
        )}

        {searched && !loading && results.length === 0 && (
          <div className="text-center py-12 text-slate-400">
            <p className="text-sm">No algorithms found for &ldquo;{query}&rdquo;</p>
            <p className="mt-1 text-xs text-slate-300">Try a different term or browse by category</p>
          </div>
        )}

        {results.length > 0 && (
          <>
            <p className="mb-4 text-sm text-slate-400">
              {results.length} result{results.length !== 1 ? 's' : ''} for &ldquo;{query}&rdquo;
            </p>
            <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
              {results.map((alg) => (
                <AlgorithmCard key={alg.slug} algorithm={alg} />
              ))}
            </div>
          </>
        )}
      </div>
    </div>
  )
}
