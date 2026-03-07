'use client'

import { cn } from '@/lib/utils'

type CalloutType = 'info' | 'warning' | 'tip' | 'danger'

const CALLOUT_STYLES: Record<CalloutType, string> = {
  info: 'border-blue-200 bg-blue-50 text-blue-900',
  warning: 'border-yellow-200 bg-yellow-50 text-yellow-900',
  tip: 'border-green-200 bg-green-50 text-green-900',
  danger: 'border-red-200 bg-red-50 text-red-900',
}

interface CalloutProps {
  type?: CalloutType
  title?: string
  children: React.ReactNode
}

export function Callout({ type = 'info', title, children }: CalloutProps) {
  return (
    <div className={cn('my-4 rounded-md border-l-4 p-4', CALLOUT_STYLES[type])}>
      {title && <p className="mb-1 font-semibold">{title}</p>}
      <div className="text-sm">{children}</div>
    </div>
  )
}
