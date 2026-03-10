import { BookOpen, Code2, FlaskConical, Clock } from 'lucide-react'

interface StatusSummaryProps {
  total: number
  planned: number
  inProgress: number
  documented: number
  implemented: number
  labReady: number
}

export function StatusSummary({
  total,
  planned,
  inProgress,
  documented,
  implemented,
  labReady,
}: StatusSummaryProps) {
  const stats = [
    {
      label: 'Total Algorithms',
      value: total,
      icon: <Clock className="h-5 w-5 text-slate-400" />,
      color: 'border-slate-200',
    },
    {
      label: 'Documented',
      value: documented + implemented + labReady,
      icon: <BookOpen className="h-5 w-5 text-blue-500" />,
      color: 'border-blue-200',
      sub: `${Math.round(((documented + implemented + labReady) / total) * 100)}% complete`,
    },
    {
      label: 'Implemented',
      value: implemented + labReady,
      icon: <Code2 className="h-5 w-5 text-purple-500" />,
      color: 'border-purple-200',
      sub: `${Math.round(((implemented + labReady) / total) * 100)}% complete`,
    },
    {
      label: 'Lab Ready',
      value: labReady,
      icon: <FlaskConical className="h-5 w-5 text-emerald-500" />,
      color: 'border-emerald-200',
      sub: `${Math.round((labReady / total) * 100)}% complete`,
    },
  ]

  return (
    <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
      {stats.map(({ label, value, icon, color, sub }) => (
        <div
          key={label}
          className={`rounded-xl border-2 bg-white p-5 ${color}`}
        >
          <div className="flex items-center gap-2">
            {icon}
            <span className="text-sm font-medium text-slate-500">{label}</span>
          </div>
          <p className="mt-2 text-3xl font-bold text-slate-900">{value}</p>
          {sub && <p className="mt-0.5 text-xs text-slate-400">{sub}</p>}
        </div>
      ))}
    </div>
  )
}
