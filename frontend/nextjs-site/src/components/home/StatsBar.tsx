interface Stat {
  label: string
  value: string | number
  description?: string
}

interface StatsBarProps {
  stats: Stat[]
}

export function StatsBar({ stats }: StatsBarProps) {
  return (
    <div className="grid grid-cols-2 divide-x divide-slate-200 border border-slate-200 rounded-xl bg-white sm:grid-cols-4">
      {stats.map((stat, i) => (
        <div
          key={i}
          className="flex flex-col items-center px-6 py-5 text-center"
        >
          <span className="text-3xl font-bold text-slate-900">{stat.value}</span>
          <span className="mt-1 text-sm font-medium text-slate-600">{stat.label}</span>
          {stat.description && (
            <span className="mt-0.5 text-xs text-slate-400">{stat.description}</span>
          )}
        </div>
      ))}
    </div>
  )
}
