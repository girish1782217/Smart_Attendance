import { useQuery } from '@tanstack/react-query'
import { AlertTriangle, CalendarCheck, ClipboardCheck, FileEdit, Users } from 'lucide-react'

import { getFacultyDashboard } from '../../api/dashboard'
import { ErrorState } from '../../components/ErrorState'
import { LoadingState } from '../../components/LoadingState'
import { StatCard } from '../../components/StatCard'

export function FacultyDashboardPage() {
  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: ['dashboard', 'faculty'],
    queryFn: getFacultyDashboard,
  })

  if (isLoading) return <LoadingState label="Loading dashboard…" />
  if (isError) return <ErrorState error={error} onRetry={() => void refetch()} />
  if (!data) return null

  return (
    <div>
      <div>
        <h1 className="text-2xl font-semibold tracking-tight text-slate-900">Faculty Dashboard</h1>
        <p className="mt-1 text-sm text-slate-500">Your assigned sections and attendance activity.</p>
      </div>

      <div className="mt-6 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard label="Assigned Sections" value={data.assigned_sections} icon={Users} />
        <StatCard label="Today's Sessions" value={data.today_sessions} icon={CalendarCheck} />
        <StatCard label="Total Sessions Conducted" value={data.total_sessions} icon={ClipboardCheck} />
        <StatCard
          label="Students Below Threshold"
          value={data.students_below_threshold}
          icon={AlertTriangle}
          tone={data.students_below_threshold > 0 ? 'warning' : 'default'}
        />
        <StatCard
          label="Pending Corrections"
          value={data.pending_correction_requests}
          icon={FileEdit}
          tone={data.pending_correction_requests > 0 ? 'warning' : 'default'}
        />
      </div>
    </div>
  )
}
