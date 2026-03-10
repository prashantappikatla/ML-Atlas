import { notFound } from 'next/navigation'
import Link from 'next/link'
import { api } from '@/lib/api-client'
import { LabEmbed } from '@/components/mdx/LabEmbed'
import { Breadcrumbs } from '@/components/algorithm/Breadcrumbs'
import { ExternalLink } from 'lucide-react'

interface Props {
  params: Promise<{ slug: string }>
}

export const dynamic = 'force-dynamic'

export async function generateMetadata({ params }: Props) {
  const { slug } = await params
  return {
    title: slug
      .split('-')
      .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
      .join(' ') + ' Lab',
  }
}

export default async function LabPage({ params }: Props) {
  const { slug } = await params

  let lab: any = null
  try {
    lab = await api.labs.byAlgorithmSlug(slug)
  } catch {
    // Lab not found
  }

  if (!lab) notFound()

  const algorithmName = lab.algorithm_name ?? slug.split('-').map((w: string) => w.charAt(0).toUpperCase() + w.slice(1)).join(' ')

  return (
    <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
      <Breadcrumbs
        items={[
          { label: 'Labs', href: '/labs' },
          { label: algorithmName },
        ]}
      />

      <div className="mt-6 mb-4 flex items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">{algorithmName} Lab</h1>
          <p className="mt-1 text-sm text-slate-500 capitalize">
            {lab.lab_type?.replace('-', ' ')} · {lab.framework}
          </p>
        </div>
        {lab.url && (
          <a
            href={lab.url}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-1.5 rounded-lg border border-slate-200 px-4 py-2 text-sm font-medium text-slate-600 hover:bg-slate-50"
          >
            <ExternalLink className="h-4 w-4" />
            Open in new tab
          </a>
        )}
      </div>

      <LabEmbed
        url={lab.url}
        title={`${algorithmName} Lab`}
        height={700}
      />
    </div>
  )
}
