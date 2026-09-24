import { useQuery, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'

import type { AttendanceStatus } from '../../api/attendanceSessions'
import { attendanceHistoryApi } from '../../api/attendanceHistory'
import { ApiError } from '../../api/client'
import { correctionsApi } from '../../api/corrections'
import { subjectsApi } from '../../api/subjects'
import { Button } from '../../components/Button'
import { DataTable, type DataTableColumn } from '../../components/DataTable'
import { ErrorState } from '../../components/ErrorState'
import { LoadingState } from '../../components/LoadingState'
import { Modal } from '../../components/Modal'
import { PageHeader } from '../../components/PageHeader'
import { Pagination } from '../../components/Pagination'
import { SelectField } from '../../components/FormField'
import { StatCard } from '../../components/StatCard'
import { StatusBadge } from '../../components/StatusBadge'
import { useAuth } from '../../contexts/AuthContext'
import { useToast } from '../../contexts/ToastContext'
import type { AttendanceHistoryRecord } from '../../api/dashboard'

const STATUS_OPTIONS: AttendanceStatus[] = ['PRESENT', 'ABSENT', 'LATE', 'EXCUSED']

function formatPercentage(value: number | null): string {
  return value === null ? 'No data' : `${value}%`
}

export function StudentMyAttendancePage() {
  const { user } = useAuth()
  const studentId = user?.student_id

  if (!studentId) {
    return <ErrorState error={new Error('No student profile is linked to this account.')} />
  }

  return <StudentMyAttendanceContent studentId={studentId} />
}

function StudentMyAttendanceContent({ studentId }: { studentId: number }) {
  const queryClient = useQueryClient()
  const { showToast } = useToast()

  const [page, setPage] = useState(1)
  const [subjectId, setSubjectId] = useState('')
  const [fromDate, setFromDate] = useState('')
  const [toDate, setToDate] = useState('')
  const [correctionTarget, setCorrectionTarget] = useState<AttendanceHistoryRecord | null>(null)
  const [requestedStatus, setRequestedStatus] = useState<AttendanceStatus>('PRESENT')
  const [reason, setReason] = useState('')
  const [formError, setFormError] = useState<string | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)

  const { data: subjects } = useQuery({ queryKey: ['subjects', 'all'], queryFn: () => subjectsApi.list({ page_size: 100 }) })
  const subjectOptions = (subjects?.items ?? []).map((s) => ({ value: s.id, label: `${s.name} (${s.code})` }))

  const summaryQuery = useQuery({
    queryKey: ['attendance-summary', studentId],
    queryFn: () => attendanceHistoryApi.getSummary(studentId),
  })

  const filters = {
    page,
    page_size: 10,
    subject_id: subjectId || undefined,
    from_date: fromDate || undefined,
    to_date: toDate || undefined,
  }
  const historyQuery = useQuery({
    queryKey: ['attendance-history', studentId, filters],
    queryFn: () => attendanceHistoryApi.getHistory(studentId, filters),
  })

  function openCorrectionModal(record: AttendanceHistoryRecord) {
    setCorrectionTarget(record)
    setRequestedStatus('PRESENT')
    setReason('')
    setFormError(null)
  }

  async function handleSubmitCorrection() {
    if (!correctionTarget) return
    if (!reason.trim()) {
      setFormError('A reason is required.')
      return
    }
    setIsSubmitting(true)
    setFormError(null)
    try {
      await correctionsApi.create(correctionTarget.id, { requested_status: requestedStatus, reason: reason.trim() })
      showToast('Correction request submitted.', 'success')
      await queryClient.invalidateQueries({ queryKey: ['attendance-history'] })
      await queryClient.invalidateQueries({ queryKey: ['corrections'] })
      setCorrectionTarget(null)
    } catch (err) {
      setFormError(err instanceof ApiError ? err.message : 'Something went wrong. Please try again.')
    } finally {
      setIsSubmitting(false)
    }
  }

  const columns: DataTableColumn<AttendanceHistoryRecord>[] = [
    { key: 'session_date', label: 'Date' },
    { key: 'subject_name', label: 'Subject', render: (row) => `${row.subject_name} (${row.subject_code})` },
    { key: 'start_time', label: 'Time', render: (row) => `${row.start_time.slice(0, 5)}–${row.end_time.slice(0, 5)}` },
    { key: 'status', label: 'Status', render: (row) => <StatusBadge status={row.status} /> },
    {
      key: 'actions',
      label: '',
      align: 'right',
      render: (row) =>
        row.was_corrected ? (
          <span className="text-xs text-slate-400">Corrected</span>
        ) : (
          <Button variant="ghost" className="!px-2 !py-1" onClick={() => openCorrectionModal(row)}>
            Request Correction
          </Button>
        ),
    },
  ]

  return (
    <div className="flex flex-col gap-6">
      <PageHeader title="My Attendance" description="Your attendance summary and full session history." />

      {summaryQuery.isLoading && <LoadingState label="Loading summary…" />}
      {summaryQuery.isError && <ErrorState error={summaryQuery.error} onRetry={() => void summaryQuery.refetch()} />}
      {summaryQuery.data && (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
          <StatCard label="Overall Attendance" value={formatPercentage(summaryQuery.data.overall.percentage)} tone="success" />
          <StatCard
            label="Present / Total"
            value={`${summaryQuery.data.overall.present_count + summaryQuery.data.overall.late_count} / ${
              summaryQuery.data.overall.present_count + summaryQuery.data.overall.absent_count + summaryQuery.data.overall.late_count
            }`}
          />
          <StatCard label="Subjects Tracked" value={summaryQuery.data.by_subject.length} />
        </div>
      )}

      {summaryQuery.data && summaryQuery.data.by_subject.length > 0 && (
        <div className="overflow-hidden overflow-x-auto rounded-xl border border-slate-200 bg-white shadow-sm">
          <table className="min-w-full divide-y divide-slate-200 text-sm">
            <thead className="bg-slate-50">
              <tr>
                <th className="px-4 py-3 text-left font-medium text-slate-600">Subject</th>
                <th className="px-4 py-3 text-right font-medium text-slate-600">Present</th>
                <th className="px-4 py-3 text-right font-medium text-slate-600">Absent</th>
                <th className="px-4 py-3 text-right font-medium text-slate-600">Late</th>
                <th className="px-4 py-3 text-right font-medium text-slate-600">Percentage</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {summaryQuery.data.by_subject.map((subject) => (
                <tr key={subject.subject_id} className="hover:bg-slate-50/60">
                  <td className="px-4 py-3 text-slate-900">
                    {subject.subject_name} <span className="text-slate-400">({subject.subject_code})</span>
                  </td>
                  <td className="px-4 py-3 text-right tabular-nums text-slate-700">{subject.present_count}</td>
                  <td className="px-4 py-3 text-right tabular-nums text-slate-700">{subject.absent_count}</td>
                  <td className="px-4 py-3 text-right tabular-nums text-slate-700">{subject.late_count}</td>
                  <td className="px-4 py-3 text-right font-medium tabular-nums text-slate-900">
                    {formatPercentage(subject.percentage)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <div>
        <h2 className="mb-3 text-sm font-semibold text-slate-900">Session History</h2>
        <div className="mb-3 flex flex-wrap items-center gap-3">
          <SelectField
            label="Subject"
            value={subjectId}
            onChange={(event) => { setSubjectId(event.target.value); setPage(1) }}
          >
            <option value="">All Subjects</option>
            {subjectOptions.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </SelectField>
          <div className="flex items-end gap-3">
            <input type="date" value={fromDate} onChange={(e) => { setFromDate(e.target.value); setPage(1) }} className="rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 shadow-sm focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/20" />
            <input type="date" value={toDate} onChange={(e) => { setToDate(e.target.value); setPage(1) }} className="rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 shadow-sm focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/20" />
          </div>
        </div>

        <div className="overflow-hidden rounded-xl">
          <DataTable
            columns={columns}
            rows={historyQuery.data?.items ?? []}
            rowKey={(row) => row.id}
            isLoading={historyQuery.isLoading}
            error={historyQuery.isError ? historyQuery.error : undefined}
            onRetry={() => void historyQuery.refetch()}
            emptyTitle="No attendance history yet"
          />
          {historyQuery.data && historyQuery.data.total > 0 && (
            <Pagination
              page={historyQuery.data.page}
              pageSize={historyQuery.data.page_size}
              total={historyQuery.data.total}
              onPageChange={setPage}
            />
          )}
        </div>
      </div>

      {correctionTarget && (
        <Modal title="Request Correction" onClose={() => setCorrectionTarget(null)}>
          <form
            onSubmit={(event) => {
              event.preventDefault()
              void handleSubmitCorrection()
            }}
            className="flex flex-col gap-4"
          >
            <p className="text-sm text-slate-600">
              {correctionTarget.subject_name} on {correctionTarget.session_date} — currently marked{' '}
              <StatusBadge status={correctionTarget.status} />.
            </p>
            <SelectField
              label="Requested Status"
              required
              value={requestedStatus}
              onChange={(event) => setRequestedStatus(event.target.value as AttendanceStatus)}
            >
              {STATUS_OPTIONS.map((status) => (
                <option key={status} value={status}>
                  {status}
                </option>
              ))}
            </SelectField>
            <div>
              <label htmlFor="correction-reason" className="mb-1.5 block text-sm font-medium text-slate-700">
                Reason
              </label>
              <textarea
                id="correction-reason"
                value={reason}
                onChange={(event) => setReason(event.target.value)}
                rows={3}
                maxLength={1000}
                required
                className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 shadow-sm transition placeholder:text-slate-400 focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/20"
                placeholder="Explain why this record should be corrected…"
              />
            </div>
            {formError && (
              <p role="alert" className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">
                {formError}
              </p>
            )}
            <div className="mt-2 flex justify-end gap-3">
              <Button type="button" variant="secondary" onClick={() => setCorrectionTarget(null)}>
                Cancel
              </Button>
              <Button type="submit" isLoading={isSubmitting}>
                Submit Request
              </Button>
            </div>
          </form>
        </Modal>
      )}
    </div>
  )
}
