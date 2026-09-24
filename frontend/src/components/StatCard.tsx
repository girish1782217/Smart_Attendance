import type { LucideIcon } from 'lucide-react'
import { Link } from 'react-router-dom'

type Tone = 'default' | 'warning' | 'danger' | 'success'

const TONE_STYLES: Record<Tone, { icon: string; value: string }> = {
  default: { icon: 'bg-brand-50 text-brand-600', value: 'text-slate-900' },
  success: { icon: 'bg-emerald-50 text-emerald-600', value: 'text-slate-900' },
  warning: { icon: 'bg-amber-50 text-amber-600', value: 'text-amber-700' },
  danger: { icon: 'bg-red-50 text-red-600', value: 'text-red-700' },
}

export function StatCard({
  label,
  value,
  icon: Icon,
  tone = 'default',
  to,
}: {
  label: string
  value: string | number
  icon?: LucideIcon
  tone?: Tone
  /** When set, the whole card links to this route (e.g. a stat that has a dedicated page). */
  to?: string
}) {
  const styles = TONE_STYLES[tone]
  const content = (
    <div className="flex items-start justify-between">
      <div>
        <p className="text-xs font-medium uppercase tracking-wide text-slate-500">{label}</p>
        <p className={`mt-2 text-2xl font-semibold tabular-nums ${styles.value}`}>{value}</p>
      </div>
      {Icon && (
        <div className={`flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-lg ${styles.icon}`}>
          <Icon className="h-5 w-5" strokeWidth={2} />
        </div>
      )}
    </div>
  )

  if (to) {
    return (
      <Link
        to={to}
        className="block rounded-xl border border-slate-200 bg-white p-5 shadow-sm transition hover:-translate-y-0.5 hover:border-brand-200 hover:shadow-md"
      >
        {content}
      </Link>
    )
  }

  return <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm transition hover:shadow-md">{content}</div>
}
