import { useQuery } from '@tanstack/react-query'

import { getAdminDashboard } from '../../api/dashboard'
import { ErrorState } from '../../components/ErrorState'
import { LoadingState } from '../../components/LoadingState'
import { StatCard } from '../../components/StatCard'

function formatPercentage(value: number | null): string {
  return value === null ? 'No data' : `${value}%`
}

export function AdminDashboardPage() {
  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: ['dashboard', 'admin'],
    queryFn: getAdminDashboard,
  })

  if (isLoading) return <LoadingState label="Loading dashboard…" />
  if (isError) return <ErrorState error={error} onRetry={() => void refetch()} />
  if (!data) return null

  return (
    <div>
      <h1 className="text-lg font-semibold text-slate-900">Admin Dashboard</h1>
      <div className="mt-4 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard label="Total Students" value={data.total_students} />
        <StatCard label="Total Faculty" value={data.total_faculty} />
        <StatCard label="Departments" value={data.total_departments} />
        <StatCard label="Classes" value={data.total_classes} />
        <StatCard
          label="Today's Sessions"
          value={`${data.today_sessions_submitted} / ${data.today_sessions_total} submitted`}
        />
        <StatCard label="Overall Attendance" value={formatPercentage(data.overall_attendance_percentage)} />
        <StatCard
          label="Students Below Threshold"
          value={data.students_below_threshold}
          tone={data.students_below_threshold > 0 ? 'warning' : 'default'}
        />
        <StatCard
          label="Pending Corrections"
          value={data.pending_correction_requests}
          tone={data.pending_correction_requests > 0 ? 'warning' : 'default'}
        />
      </div>
    </div>
  )
}
