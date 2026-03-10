import { SearchPage as SearchPageClient } from '@/components/search/SearchPage'

export const metadata = { title: 'Search' }

export default function SearchPage() {
  return (
    <div className="mx-auto max-w-4xl px-4 py-10 sm:px-6 lg:px-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-slate-900">Search Algorithms</h1>
        <p className="mt-2 text-slate-500">
          Search across all 278 ML algorithms by name, author, or description.
        </p>
      </div>
      <SearchPageClient />
    </div>
  )
}
