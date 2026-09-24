import { useQuery } from '@tanstack/react-query'

import { getStudentDashboard } from '../../api/dashboard'
import { EmptyState } from '../../components/EmptyState'
import { ErrorState } from '../../components/ErrorState'
import { LoadingState } from '../../components/LoadingState'
import { StatCard } from '../../components/StatCard'
import { StatusBadge } from '../../components/StatusBadge'

function formatPercentage(value: number | null): string {
  return value === null ? 'No data' : `${value}%`
}

export function StudentDashboardPage() {
  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: ['dashboard', 'student'],
    queryFn: getStudentDashboard,
  })

  if (isLoading) return <LoadingState label="Loading your dashboard…" />
  if (isError) return <ErrorState error={error} onRetry={() => void refetch()} />
  if (!data) return null

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-lg font-semibold text-slate-900">My Dashboard</h1>
        {data.is_low_attendance && (
          <p role="alert" className="mt-2 rounded-md bg-red-50 px-3 py-2 text-sm text-red-800">
            Your overall attendance is below the {data.threshold}% threshold. Please contact your
            department if you believe this is incorrect.
          </p>
        )}
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <StatCard
          label="Overall Attendance"
          value={formatPercentage(data.overall.percentage)}
          tone={data.is_low_attendance ? 'danger' : 'default'}
        />
        <StatCard label="Present / Total" value={`${data.overall.present_count + data.overall.late_count} / ${data.overall.present_count + data.overall.absent_count + data.overall.late_count}`} />
        <StatCard label="Pending Correction Requests" value={data.pending_correction_requests} />
      </div>

      <section>
        <h2 className="text-sm font-semibold text-slate-900">Subject-wise Attendance</h2>
        {data.by_subject.length === 0 ? (
          <EmptyState title="No subject data yet" description="Attendance will appear here once sessions are recorded." />
        ) : (
          <div className="mt-2 overflow-x-auto rounded-lg border border-slate-200 bg-white">
            <table className="min-w-full divide-y divide-slate-200 text-sm">
              <thead className="bg-slate-50">
                <tr>
                  <th className="px-4 py-2 text-left font-medium text-slate-600">Subject</th>
                  <th className="px-4 py-2 text-right font-medium text-slate-600">Present</th>
                  <th className="px-4 py-2 text-right font-medium text-slate-600">Absent</th>
                  <th className="px-4 py-2 text-right font-medium text-slate-600">Late</th>
                  <th className="px-4 py-2 text-right font-medium text-slate-600">Percentage</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {data.by_subject.map((subject) => (
                  <tr key={subject.subject_id}>
                    <td className="px-4 py-2 text-slate-900">
                      {subject.subject_name} <span className="text-slate-400">({subject.subject_code})</span>
                    </td>
                    <td className="px-4 py-2 text-right text-slate-700">{subject.present_count}</td>
                    <td className="px-4 py-2 text-right text-slate-700">{subject.absent_count}</td>
                    <td className="px-4 py-2 text-right text-slate-700">{subject.late_count}</td>
                    <td className="px-4 py-2 text-right font-medium text-slate-900">
                      {formatPercentage(subject.percentage)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      <section>
        <h2 className="text-sm font-semibold text-slate-900">Recent Attendance</h2>
        {data.recent_attendance.length === 0 ? (
          <EmptyState title="No recent attendance" />
        ) : (
          <ul className="mt-2 divide-y divide-slate-100 rounded-lg border border-slate-200 bg-white">
            {data.recent_attendance.map((record) => (
              <li key={record.id} className="flex items-center justify-between px-4 py-3 text-sm">
                <div>
                  <p className="font-medium text-slate-900">
                    {record.subject_name} <span className="text-slate-400">({record.subject_code})</span>
                  </p>
                  <p className="text-slate-500">{record.session_date}</p>
                </div>
                <StatusBadge status={record.status} />
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  )
}
