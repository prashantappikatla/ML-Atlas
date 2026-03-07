export default function HomePage() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center p-8">
      <h1 className="text-4xl font-bold">ML Atlas</h1>
      <p className="mt-4 text-lg text-gray-600">
        Documentation and interactive labs for 278 machine learning algorithms.
      </p>
      <div className="mt-8 flex gap-4">
        <a
          href="/algorithms"
          className="rounded-md bg-blue-600 px-6 py-3 text-white hover:bg-blue-700"
        >
          Browse Algorithms
        </a>
        <a
          href="/progress"
          className="rounded-md border border-gray-300 px-6 py-3 text-gray-700 hover:bg-gray-50"
        >
          View Progress
        </a>
      </div>
    </div>
  )
}
