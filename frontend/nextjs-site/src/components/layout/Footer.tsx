import Link from 'next/link'
import { Brain } from 'lucide-react'
import { CATEGORIES } from '@/lib/categories'

export function Footer() {
  return (
    <footer className="border-t border-slate-200 bg-slate-50">
      <div className="mx-auto max-w-7xl px-4 py-12 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 gap-8 md:grid-cols-4">
          {/* Brand */}
          <div className="md:col-span-1">
            <Link href="/" className="flex items-center gap-2 font-semibold text-slate-900">
              <Brain className="h-5 w-5 text-indigo-600" />
              <span>ML Atlas</span>
            </Link>
            <p className="mt-3 text-sm text-slate-500">
              Documentation and interactive labs for 278 machine learning algorithms.
            </p>
          </div>

          {/* Algorithms */}
          <div>
            <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-400">
              Categories
            </h3>
            <ul className="mt-3 space-y-2">
              {CATEGORIES.slice(0, 5).map((cat) => (
                <li key={cat.slug}>
                  <Link
                    href={`/algorithms/${cat.slug}`}
                    className="text-sm text-slate-500 hover:text-slate-900"
                  >
                    {cat.name}
                  </Link>
                </li>
              ))}
            </ul>
          </div>

          <div>
            <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-400">
              &nbsp;
            </h3>
            <ul className="mt-3 space-y-2">
              {CATEGORIES.slice(5).map((cat) => (
                <li key={cat.slug}>
                  <Link
                    href={`/algorithms/${cat.slug}`}
                    className="text-sm text-slate-500 hover:text-slate-900"
                  >
                    {cat.name}
                  </Link>
                </li>
              ))}
            </ul>
          </div>

          {/* Platform */}
          <div>
            <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-400">
              Platform
            </h3>
            <ul className="mt-3 space-y-2">
              {[
                { href: '/algorithms', label: 'Browse Algorithms' },
                { href: '/labs', label: 'Interactive Labs' },
                { href: '/progress', label: 'Progress Tracker' },
                { href: '/search', label: 'Search' },
              ].map(({ href, label }) => (
                <li key={href}>
                  <Link href={href} className="text-sm text-slate-500 hover:text-slate-900">
                    {label}
                  </Link>
                </li>
              ))}
            </ul>
          </div>
        </div>

        <div className="mt-8 border-t border-slate-200 pt-6 flex items-center justify-between">
          <p className="text-xs text-slate-400">
            Built for deep learning of machine learning concepts.
          </p>
          <p className="text-xs text-slate-400">278 algorithms across 10 categories</p>
        </div>
      </div>
    </footer>
  )
}
