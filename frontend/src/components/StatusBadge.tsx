const STYLES_BY_STATUS: Record<string, string> = {
  PRESENT: 'bg-emerald-50 text-emerald-700 ring-emerald-600/20',
  ABSENT: 'bg-red-50 text-red-700 ring-red-600/20',
  LATE: 'bg-amber-50 text-amber-700 ring-amber-600/20',
  EXCUSED: 'bg-slate-100 text-slate-600 ring-slate-500/20',
  SCHEDULED: 'bg-blue-50 text-blue-700 ring-blue-600/20',
  SUBMITTED: 'bg-emerald-50 text-emerald-700 ring-emerald-600/20',
  PENDING: 'bg-amber-50 text-amber-700 ring-amber-600/20',
  APPROVED: 'bg-emerald-50 text-emerald-700 ring-emerald-600/20',
  REJECTED: 'bg-red-50 text-red-700 ring-red-600/20',
  ACTIVE: 'bg-emerald-50 text-emerald-700 ring-emerald-600/20',
  INACTIVE: 'bg-slate-100 text-slate-600 ring-slate-500/20',
}

export function StatusBadge({ status }: { status: string }) {
  const classes = STYLES_BY_STATUS[status] ?? 'bg-slate-100 text-slate-600 ring-slate-500/20'
  return (
    <span
      className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ring-1 ring-inset ${classes}`}
    >
      {status}
    </span>
  )
}
