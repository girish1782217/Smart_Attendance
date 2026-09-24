export function StatCard({
  label,
  value,
  tone = 'default',
}: {
  label: string
  value: string | number
  tone?: 'default' | 'warning' | 'danger'
}) {
  const valueClasses =
    tone === 'danger' ? 'text-red-600' : tone === 'warning' ? 'text-amber-600' : 'text-slate-900'
  return (
    <div className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
      <p className="text-xs font-medium uppercase tracking-wide text-slate-500">{label}</p>
      <p className={`mt-1 text-2xl font-semibold ${valueClasses}`}>{value}</p>
    </div>
  )
}
