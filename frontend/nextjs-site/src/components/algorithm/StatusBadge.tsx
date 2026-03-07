import { AlgorithmStatus } from '@/types/mdx'
import { cn } from '@/lib/utils'

const STATUS_STYLES: Record<AlgorithmStatus, string> = {
  planned: 'bg-gray-100 text-gray-600',
  'in-progress': 'bg-yellow-100 text-yellow-700',
  documented: 'bg-blue-100 text-blue-700',
  implemented: 'bg-purple-100 text-purple-700',
  'lab-ready': 'bg-green-100 text-green-700',
}

interface StatusBadgeProps {
  status: AlgorithmStatus
  className?: string
}

export function StatusBadge({ status, className }: StatusBadgeProps) {
  return (
    <span
      className={cn(
        'inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium',
        STATUS_STYLES[status],
        className
      )}
    >
      {status}
    </span>
  )
}
