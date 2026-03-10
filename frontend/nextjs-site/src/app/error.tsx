'use client'

import Link from 'next/link'

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string }
  reset: () => void
}) {
  return (
    <div className="flex min-h-[60vh] flex-col items-center justify-center px-4 text-center">
      <p className="text-sm font-semibold uppercase tracking-widest text-red-500">Error</p>
      <h1 className="mt-2 text-3xl font-bold text-slate-900">Something went wrong</h1>
      <p className="mt-3 text-slate-500">
        {error.message || 'An unexpected error occurred. Please try again.'}
      </p>
      <div className="mt-6 flex gap-3">
        <button
          onClick={reset}
          className="rounded-lg bg-indigo-600 px-5 py-2.5 text-sm font-semibold text-white hover:bg-indigo-700"
        >
          Try again
        </button>
        <Link
          href="/"
          className="rounded-lg border border-slate-200 px-5 py-2.5 text-sm font-semibold text-slate-700 hover:bg-slate-50"
        >
          Go home
        </Link>
      </div>
    </div>
  )
}
