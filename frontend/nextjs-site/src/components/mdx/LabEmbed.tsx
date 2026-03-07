'use client'

interface LabEmbedProps {
  url: string
  title?: string
  height?: number
}

export function LabEmbed({ url, title = 'Interactive Lab', height = 700 }: LabEmbedProps) {
  if (!url) {
    return (
      <div className="flex items-center justify-center rounded-lg border-2 border-dashed border-gray-200 bg-gray-50 p-12 text-gray-400">
        Lab not yet available
      </div>
    )
  }

  return (
    <div className="overflow-hidden rounded-lg border border-gray-200">
      <iframe
        src={url}
        title={title}
        width="100%"
        height={height}
        className="block"
        loading="lazy"
      />
    </div>
  )
}
