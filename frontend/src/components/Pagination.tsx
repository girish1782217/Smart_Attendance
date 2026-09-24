export function Pagination({
  page,
  pageSize,
  total,
  onPageChange,
}: {
  page: number
  pageSize: number
  total: number
  onPageChange: (page: number) => void
}) {
  const totalPages = Math.max(1, Math.ceil(total / pageSize))
  if (totalPages <= 1) return null

  const start = total === 0 ? 0 : (page - 1) * pageSize + 1
  const end = Math.min(page * pageSize, total)

  return (
    <nav className="flex items-center justify-between border-t border-slate-200 px-2 py-3" aria-label="Pagination">
      <p className="text-sm text-slate-600">
        Showing <span className="font-medium">{start}</span>–<span className="font-medium">{end}</span> of{' '}
        <span className="font-medium">{total}</span>
      </p>
      <div className="flex gap-2">
        <button
          type="button"
          onClick={() => onPageChange(page - 1)}
          disabled={page <= 1}
          className="rounded-md border border-slate-300 px-3 py-1.5 text-sm font-medium text-slate-700 disabled:cursor-not-allowed disabled:opacity-40 hover:bg-slate-50"
        >
          Previous
        </button>
        <span className="px-2 py-1.5 text-sm text-slate-500">
          Page {page} of {totalPages}
        </span>
        <button
          type="button"
          onClick={() => onPageChange(page + 1)}
          disabled={page >= totalPages}
          className="rounded-md border border-slate-300 px-3 py-1.5 text-sm font-medium text-slate-700 disabled:cursor-not-allowed disabled:opacity-40 hover:bg-slate-50"
        >
          Next
        </button>
      </div>
    </nav>
  )
}
