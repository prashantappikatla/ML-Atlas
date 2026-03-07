export const dynamic = 'force-dynamic'
export const metadata = { title: 'Progress' }

export default async function ProgressPage() {
  // Fetch from FastAPI at request time (dynamic page)
  // const data = await api.status.list()

  return (
    <div className="mx-auto max-w-5xl p-8">
      <h1 className="text-3xl font-bold">Implementation Progress</h1>
      <p className="mt-2 text-gray-600">Track documentation and lab completion across all 278 algorithms.</p>
      {/* Progress dashboard will go here */}
    </div>
  )
}
