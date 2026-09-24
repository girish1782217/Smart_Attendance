const COLOR_BY_STATUS: Record<string, string> = {
  PRESENT: 'bg-emerald-100 text-emerald-800',
  ABSENT: 'bg-red-100 text-red-800',
  LATE: 'bg-amber-100 text-amber-800',
  EXCUSED: 'bg-slate-100 text-slate-700',
  SCHEDULED: 'bg-blue-100 text-blue-800',
  SUBMITTED: 'bg-emerald-100 text-emerald-800',
  PENDING: 'bg-amber-100 text-amber-800',
  APPROVED: 'bg-emerald-100 text-emerald-800',
  REJECTED: 'bg-red-100 text-red-800',
  ACTIVE: 'bg-emerald-100 text-emerald-800',
  INACTIVE: 'bg-slate-100 text-slate-600',
}

export function StatusBadge({ status }: { status: string }) {
  const colorClasses = COLOR_BY_STATUS[status] ?? 'bg-slate-100 text-slate-700'
  return (
    <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${colorClasses}`}>
      {status}
    </span>
  )
}
