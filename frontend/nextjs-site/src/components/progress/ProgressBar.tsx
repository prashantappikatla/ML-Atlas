interface ProgressBarProps {
  value: number
  max: number
  color?: string
  className?: string
}

export function ProgressBar({ value, max, color = '#4f46e5', className = '' }: ProgressBarProps) {
  const percent = max > 0 ? Math.round((value / max) * 100) : 0
  return (
    <div className={`h-2 overflow-hidden rounded-full bg-slate-100 ${className}`}>
      <div
        className="h-full rounded-full transition-all"
        style={{ width: `${percent}%`, backgroundColor: color }}
      />
    </div>
  )
}
