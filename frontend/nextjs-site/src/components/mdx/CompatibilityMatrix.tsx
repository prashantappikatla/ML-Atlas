import { Check, X } from 'lucide-react'

interface CompatibilityMatrixProps {
  tabular?: boolean
  image?: boolean
  text?: boolean
  timeseries?: boolean
  graph?: boolean
}

const ROWS = [
  { key: 'tabular', label: 'Tabular' },
  { key: 'image', label: 'Images' },
  { key: 'text', label: 'Text / NLP' },
  { key: 'timeseries', label: 'Time Series' },
  { key: 'graph', label: 'Graph / Network' },
] as const

export function CompatibilityMatrix(props: CompatibilityMatrixProps) {
  return (
    <div className="not-prose my-4 overflow-hidden rounded-lg border border-slate-200">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-slate-200 bg-slate-50">
            <th className="px-4 py-2.5 text-left text-xs font-semibold uppercase tracking-wider text-slate-500">
              Data Type
            </th>
            <th className="px-4 py-2.5 text-left text-xs font-semibold uppercase tracking-wider text-slate-500">
              Compatible
            </th>
          </tr>
        </thead>
        <tbody>
          {ROWS.map(({ key, label }, i) => {
            const compatible = props[key] ?? false
            return (
              <tr
                key={key}
                className={i % 2 === 1 ? 'bg-slate-50/50' : 'bg-white'}
              >
                <td className="px-4 py-2.5 font-medium text-slate-700">{label}</td>
                <td className="px-4 py-2.5">
                  {compatible ? (
                    <span className="inline-flex items-center gap-1 text-emerald-600">
                      <Check className="h-4 w-4" />
                      <span className="text-xs font-medium">Yes</span>
                    </span>
                  ) : (
                    <span className="inline-flex items-center gap-1 text-slate-400">
                      <X className="h-4 w-4" />
                      <span className="text-xs font-medium">No</span>
                    </span>
                  )}
                </td>
              </tr>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}
