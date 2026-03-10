'use client'

import { CATEGORIES } from '@/lib/categories'

export interface FilterState {
  categories: string[]
  complexity: string[]
  status: string[]
  compatibility: string[]
}

interface FilterSidebarProps {
  filters: FilterState
  onChange: (filters: FilterState) => void
  counts?: {
    total: number
    filtered: number
  }
}

const COMPLEXITY_OPTIONS = [
  { value: 'low', label: 'Low' },
  { value: 'medium', label: 'Medium' },
  { value: 'high', label: 'High' },
]

const STATUS_OPTIONS = [
  { value: 'planned', label: 'Planned' },
  { value: 'in-progress', label: 'In Progress' },
  { value: 'documented', label: 'Documented' },
  { value: 'implemented', label: 'Implemented' },
  { value: 'lab-ready', label: 'Lab Ready' },
]

const COMPATIBILITY_OPTIONS = [
  { value: 'tabular', label: 'Tabular' },
  { value: 'image', label: 'Images' },
  { value: 'text', label: 'Text / NLP' },
  { value: 'timeseries', label: 'Time Series' },
  { value: 'graph', label: 'Graph' },
]

function FilterSection({
  title,
  children,
}: {
  title: string
  children: React.ReactNode
}) {
  return (
    <div>
      <h3 className="mb-2 text-xs font-semibold uppercase tracking-wider text-slate-400">
        {title}
      </h3>
      <div className="space-y-1">{children}</div>
    </div>
  )
}

function Checkbox({
  checked,
  label,
  onChange,
}: {
  checked: boolean
  label: string
  onChange: () => void
}) {
  return (
    <label className="flex cursor-pointer items-center gap-2 rounded px-1 py-0.5 hover:bg-slate-50">
      <input
        type="checkbox"
        checked={checked}
        onChange={onChange}
        className="h-3.5 w-3.5 rounded border-slate-300 text-indigo-600 focus:ring-indigo-500"
      />
      <span className="text-sm text-slate-600">{label}</span>
    </label>
  )
}

function toggle(arr: string[], val: string): string[] {
  return arr.includes(val) ? arr.filter((v) => v !== val) : [...arr, val]
}

export function FilterSidebar({ filters, onChange, counts }: FilterSidebarProps) {
  const hasFilters =
    filters.categories.length > 0 ||
    filters.complexity.length > 0 ||
    filters.status.length > 0 ||
    filters.compatibility.length > 0

  return (
    <aside className="w-56 shrink-0 space-y-5">
      <div className="flex items-center justify-between">
        <h2 className="text-sm font-semibold text-slate-900">Filters</h2>
        {hasFilters && (
          <button
            onClick={() =>
              onChange({ categories: [], complexity: [], status: [], compatibility: [] })
            }
            className="text-xs text-indigo-600 hover:text-indigo-800"
          >
            Clear all
          </button>
        )}
      </div>

      {counts && (
        <p className="text-xs text-slate-400">
          {counts.filtered} of {counts.total} algorithms
        </p>
      )}

      <FilterSection title="Category">
        {CATEGORIES.map((cat) => (
          <Checkbox
            key={cat.slug}
            checked={filters.categories.includes(cat.slug)}
            label={cat.name}
            onChange={() =>
              onChange({ ...filters, categories: toggle(filters.categories, cat.slug) })
            }
          />
        ))}
      </FilterSection>

      <FilterSection title="Complexity">
        {COMPLEXITY_OPTIONS.map(({ value, label }) => (
          <Checkbox
            key={value}
            checked={filters.complexity.includes(value)}
            label={label}
            onChange={() =>
              onChange({ ...filters, complexity: toggle(filters.complexity, value) })
            }
          />
        ))}
      </FilterSection>

      <FilterSection title="Status">
        {STATUS_OPTIONS.map(({ value, label }) => (
          <Checkbox
            key={value}
            checked={filters.status.includes(value)}
            label={label}
            onChange={() => onChange({ ...filters, status: toggle(filters.status, value) })}
          />
        ))}
      </FilterSection>

      <FilterSection title="Data Type">
        {COMPATIBILITY_OPTIONS.map(({ value, label }) => (
          <Checkbox
            key={value}
            checked={filters.compatibility.includes(value)}
            label={label}
            onChange={() =>
              onChange({ ...filters, compatibility: toggle(filters.compatibility, value) })
            }
          />
        ))}
      </FilterSection>
    </aside>
  )
}
