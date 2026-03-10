import Link from 'next/link'
import { Search } from 'lucide-react'

export default function NotFound() {
  return (
    <div className="flex min-h-[60vh] flex-col items-center justify-center px-4 text-center">
      <p className="text-sm font-semibold uppercase tracking-widest text-indigo-600">404</p>
      <h1 className="mt-2 text-3xl font-bold text-slate-900">Page not found</h1>
      <p className="mt-3 text-slate-500">
        The algorithm or page you&apos;re looking for doesn&apos;t exist yet.
      </p>
      <div className="mt-6 flex gap-3">
        <Link
          href="/algorithms"
          className="rounded-lg bg-indigo-600 px-5 py-2.5 text-sm font-semibold text-white hover:bg-indigo-700"
        >
          Browse Algorithms
        </Link>
        <Link
          href="/search"
          className="flex items-center gap-1.5 rounded-lg border border-slate-200 px-5 py-2.5 text-sm font-semibold text-slate-700 hover:bg-slate-50"
        >
          <Search className="h-4 w-4" />
          Search
        </Link>
      </div>
    </div>
  )
}
