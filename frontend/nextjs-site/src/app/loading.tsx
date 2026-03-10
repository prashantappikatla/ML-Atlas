export default function Loading() {
  return (
    <div className="flex min-h-[60vh] items-center justify-center">
      <div className="flex items-center gap-2 text-slate-400">
        <div className="h-5 w-5 animate-spin rounded-full border-2 border-slate-200 border-t-indigo-600" />
        <span className="text-sm">Loading…</span>
      </div>
    </div>
  )
}
