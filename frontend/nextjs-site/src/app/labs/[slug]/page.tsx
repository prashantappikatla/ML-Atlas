interface Props {
  params: Promise<{ slug: string }>
}

export default async function LabPage({ params }: Props) {
  const { slug } = await params

  return (
    <div className="mx-auto max-w-7xl p-8">
      <h1 className="text-2xl font-bold capitalize">{slug.replace(/-/g, ' ')} Lab</h1>
      {/* LabEmbed component will render the iframe here */}
    </div>
  )
}
