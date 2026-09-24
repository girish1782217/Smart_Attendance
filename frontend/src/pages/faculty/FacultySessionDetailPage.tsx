import { useQuery, useQueryClient } from '@tanstack/react-query'
import { ArrowLeft } from 'lucide-react'
import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'

import type { AttendanceStatus } from '../../api/attendanceSessions'
import { attendanceSessionsApi } from '../../api/attendanceSessions'
import { ApiError } from '../../api/client'
import { Button } from '../../components/Button'
import { ErrorState } from '../../components/ErrorState'
import { LoadingState } from '../../components/LoadingState'
import { PageHeader } from '../../components/PageHeader'
import { StatusBadge } from '../../components/StatusBadge'
import { useToast } from '../../contexts/ToastContext'

const STATUS_OPTIONS: AttendanceStatus[] = ['PRESENT', 'ABSENT', 'LATE', 'EXCUSED']

export function FacultySessionDetailPage() {
  const { sessionId } = useParams<{ sessionId: string }>()
  const id = Number(sessionId)
  const queryClient = useQueryClient()
  const { showToast } = useToast()

  const [statuses, setStatuses] = useState<Record<number, AttendanceStatus>>({})
  const [isSaving, setIsSaving] = useState(false)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [actionError, setActionError] = useState<string | null>(null)

  const sessionQuery = useQuery({
    queryKey: ['attendance-session', id],
    queryFn: () => attendanceSessionsApi.get(id),
  })
  const rosterQuery = useQuery({
    queryKey: ['attendance-session', id, 'roster'],
    queryFn: () => attendanceSessionsApi.getRoster(id),
  })
  const recordsQuery = useQuery({
    queryKey: ['attendance-session', id, 'records'],
    queryFn: () => attendanceSessionsApi.getRecords(id),
  })

  useEffect(() => {
    if (!rosterQuery.data) return
    const initial: Record<number, AttendanceStatus> = {}
    for (const student of rosterQuery.data) {
      const existing = recordsQuery.data?.find((record) => record.student_id === student.id)
      initial[student.id] = existing?.status ?? 'PRESENT'
    }
    setStatuses(initial)
    // Only re-derive when the roster/records themselves change, not on every render.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [rosterQuery.data, recordsQuery.data])

  if (sessionQuery.isLoading || rosterQuery.isLoading || recordsQuery.isLoading) {
    return <LoadingState label="Loading session…" />
  }
  if (sessionQuery.isError) {
    return <ErrorState error={sessionQuery.error} onRetry={() => void sessionQuery.refetch()} />
  }
  if (!sessionQuery.data || !rosterQuery.data) return null

  const session = sessionQuery.data
  const roster = rosterQuery.data
  const isReadOnly = session.status === 'SUBMITTED'

  async function handleSave() {
    setActionError(null)
    setIsSaving(true)
    try {
      const records = roster.map((student) => ({ student_id: student.id, status: statuses[student.id] ?? 'PRESENT' }))
      await attendanceSessionsApi.markRecords(id, records)
      showToast('Attendance saved.', 'success')
      await queryClient.invalidateQueries({ queryKey: ['attendance-session', id, 'records'] })
    } catch (err) {
      setActionError(err instanceof ApiError ? err.message : 'Something went wrong. Please try again.')
    } finally {
      setIsSaving(false)
    }
  }

  async function handleSubmit() {
    setActionError(null)
    setIsSubmitting(true)
    try {
      await handleSave()
      await attendanceSessionsApi.submit(id)
      showToast('Session submitted.', 'success')
      await queryClient.invalidateQueries({ queryKey: ['attendance-session', id] })
      await queryClient.invalidateQueries({ queryKey: ['attendance-sessions'] })
    } catch (err) {
      setActionError(err instanceof ApiError ? err.message : 'Something went wrong. Please try again.')
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div className="flex flex-col gap-5">
      <div>
        <Link to="/faculty/sessions" className="inline-flex items-center gap-1.5 text-sm text-slate-500 hover:text-slate-700">
          <ArrowLeft className="h-4 w-4" strokeWidth={2} />
          Back to sessions
        </Link>
      </div>

      <PageHeader
        title={`${session.subject_name} (${session.subject_code})`}
        description={`${session.section_name} · ${session.session_date} · ${session.start_time.slice(0, 5)}–${session.end_time.slice(0, 5)}`}
        action={<StatusBadge status={session.status} />}
      />

      {actionError && (
        <p role="alert" className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">
          {actionError}
        </p>
      )}

      <div className="overflow-hidden overflow-x-auto rounded-xl border border-slate-200 bg-white shadow-sm">
        <table className="min-w-full divide-y divide-slate-200 text-sm">
          <thead className="bg-slate-50">
            <tr>
              <th className="px-4 py-3 text-left font-medium text-slate-600">Roll Number</th>
              <th className="px-4 py-3 text-left font-medium text-slate-600">Name</th>
              <th className="px-4 py-3 text-right font-medium text-slate-600">Status</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {roster.map((student) => (
              <tr key={student.id} className="hover:bg-slate-50/60">
                <td className="px-4 py-3 text-slate-700">{student.roll_number}</td>
                <td className="px-4 py-3 text-slate-900">{student.full_name}</td>
                <td className="px-4 py-3 text-right">
                  {isReadOnly ? (
                    <StatusBadge status={statuses[student.id] ?? 'PRESENT'} />
                  ) : (
                    <select
                      value={statuses[student.id] ?? 'PRESENT'}
                      onChange={(event) =>
                        setStatuses((prev) => ({ ...prev, [student.id]: event.target.value as AttendanceStatus }))
                      }
                      className="rounded-lg border border-slate-300 bg-white px-2.5 py-1.5 text-sm text-slate-900 shadow-sm focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/20"
                    >
                      {STATUS_OPTIONS.map((status) => (
                        <option key={status} value={status}>
                          {status}
                        </option>
                      ))}
                    </select>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {!isReadOnly && (
        <div className="flex justify-end gap-3">
          <Button variant="secondary" onClick={() => void handleSave()} isLoading={isSaving}>
            Save Attendance
          </Button>
          <Button onClick={() => void handleSubmit()} isLoading={isSubmitting}>
            Submit Session
          </Button>
        </div>
      )}
    </div>
  )
}
