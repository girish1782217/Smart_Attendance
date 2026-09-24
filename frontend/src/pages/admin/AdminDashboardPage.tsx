import { useQuery } from '@tanstack/react-query'
import {
  AlertTriangle,
  Building2,
  CalendarCheck,
  ClipboardList,
  FileEdit,
  GraduationCap,
  TrendingUp,
  UserCog,
} from 'lucide-react'

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
      <div>
        <h1 className="text-2xl font-semibold tracking-tight text-slate-900">Admin Dashboard</h1>
        <p className="mt-1 text-sm text-slate-500">
          A college-wide snapshot of enrollment, attendance, and pending reviews.
        </p>
      </div>

      <div className="mt-6 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard label="Total Students" value={data.total_students} icon={GraduationCap} to="/admin/students" />
        <StatCard label="Total Faculty" value={data.total_faculty} icon={UserCog} to="/admin/faculty" />
        <StatCard label="Departments" value={data.total_departments} icon={Building2} to="/admin/departments" />
        <StatCard label="Classes" value={data.total_classes} icon={ClipboardList} to="/admin/classes" />
        <StatCard
          label="Today's Sessions"
          value={`${data.today_sessions_submitted} / ${data.today_sessions_total} submitted`}
          icon={CalendarCheck}
        />
        <StatCard
          label="Overall Attendance"
          value={formatPercentage(data.overall_attendance_percentage)}
          icon={TrendingUp}
          tone="success"
          to="/admin/reports"
        />
        <StatCard
          label="Students Below Threshold"
          value={data.students_below_threshold}
          icon={AlertTriangle}
          tone={data.students_below_threshold > 0 ? 'warning' : 'default'}
          to="/admin/reports"
        />
        <StatCard
          label="Pending Corrections"
          value={data.pending_correction_requests}
          icon={FileEdit}
          tone={data.pending_correction_requests > 0 ? 'warning' : 'default'}
          to="/admin/corrections"
        />
      </div>
    </div>
  )
}
