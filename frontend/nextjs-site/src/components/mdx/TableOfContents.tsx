'use client'

import { useEffect, useState } from 'react'

interface TocItem {
  id: string
  text: string
  level: number
}

interface TableOfContentsProps {
  headings: TocItem[]
}

export function TableOfContents({ headings }: TableOfContentsProps) {
  const [activeId, setActiveId] = useState<string>('')

  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        for (const entry of entries) {
          if (entry.isIntersecting) {
            setActiveId(entry.target.id)
          }
        }
      },
      { rootMargin: '-80px 0% -70% 0%' }
    )

    headings.forEach(({ id }) => {
      const el = document.getElementById(id)
      if (el) observer.observe(el)
    })

    return () => observer.disconnect()
  }, [headings])

  if (headings.length === 0) return null

  return (
    <nav aria-label="Table of contents">
      <p className="mb-3 text-xs font-semibold uppercase tracking-wider text-slate-400">
        On this page
      </p>
      <ul className="space-y-1">
        {headings.map(({ id, text, level }) => (
          <li key={id} style={{ paddingLeft: `${(level - 2) * 12}px` }}>
            <a
              href={`#${id}`}
              className={`block py-0.5 text-sm transition-colors ${
                activeId === id
                  ? 'font-medium text-indigo-600'
                  : 'text-slate-500 hover:text-slate-900'
              }`}
            >
              {text}
            </a>
          </li>
        ))}
      </ul>
    </nav>
  )
}
