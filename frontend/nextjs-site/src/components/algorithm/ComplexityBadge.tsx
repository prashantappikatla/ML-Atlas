import { Complexity } from '@/types/mdx'
import { cn } from '@/lib/utils'

const COMPLEXITY_STYLES: Record<Complexity, string> = {
  low: 'bg-green-100 text-green-700',
  medium: 'bg-yellow-100 text-yellow-700',
  high: 'bg-red-100 text-red-700',
}

interface ComplexityBadgeProps {
  complexity: Complexity
  className?: string
}

export function ComplexityBadge({ complexity, className }: ComplexityBadgeProps) {
  return (
    <span
      className={cn(
        'inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium capitalize',
        COMPLEXITY_STYLES[complexity],
        className
      )}
    >
      {complexity}
    </span>
  )
}
