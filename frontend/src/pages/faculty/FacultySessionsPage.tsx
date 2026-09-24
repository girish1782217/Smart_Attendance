import { useQuery, useQueryClient } from '@tanstack/react-query'
import { Plus } from 'lucide-react'
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'

import { attendanceSessionsApi, type AttendanceSession } from '../../api/attendanceSessions'
import { ApiError } from '../../api/client'
import { facultyAssignmentsApi } from '../../api/facultyAssignments'
import { sectionsApi } from '../../api/sections'
import { subjectsApi } from '../../api/subjects'
import { Button } from '../../components/Button'
import { DataTable, type DataTableColumn } from '../../components/DataTable'
import { FormField, SelectField } from '../../components/FormField'
import { LoadingState } from '../../components/LoadingState'
import { Modal } from '../../components/Modal'
import { PageHeader } from '../../components/PageHeader'
import { Pagination } from '../../components/Pagination'
import { StatusBadge } from '../../components/StatusBadge'
import { useToast } from '../../contexts/ToastContext'

const EMPTY_FORM = { assignment_id: '', session_date: '', start_time: '', end_time: '' }

export function FacultySessionsPage() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const { showToast } = useToast()

  const [page, setPage] = useState(1)
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [formValues, setFormValues] = useState(EMPTY_FORM)
  const [formError, setFormError] = useState<string | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)

  const { data: assignments, isLoading: isLoadingAssignments } = useQuery({
    queryKey: ['faculty-assignments', 'own'],
    queryFn: () => facultyAssignmentsApi.list({ page_size: 100 }),
  })
  const { data: subjects } = useQuery({ queryKey: ['subjects', 'all'], queryFn: () => subjectsApi.list({ page_size: 100 }) })
  const { data: sections } = useQuery({ queryKey: ['sections', 'all'], queryFn: () => sectionsApi.list({ page_size: 100 }) })

  const subjectNameById = new Map((subjects?.items ?? []).map((s) => [s.id, `${s.name} (${s.code})`]))
  const sectionNameById = new Map((sections?.items ?? []).map((s) => [s.id, s.name]))

  const activeAssignments = (assignments?.items ?? []).filter((a) => a.is_active)
  const assignmentOptions = activeAssignments.map((assignment) => ({
    value: assignment.id,
    label: `${subjectNameById.get(assignment.subject_id) ?? 'Subject'} — ${sectionNameById.get(assignment.section_id) ?? 'Section'}`,
  }))

  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: ['attendance-sessions', page],
    queryFn: () => attendanceSessionsApi.list({ page, page_size: 10 }),
  })

  function openModal() {
    setFormValues(EMPTY_FORM)
    setFormError(null)
    setIsModalOpen(true)
  }

  async function handleSubmit() {
    setFormError(null)
    const assignment = activeAssignments.find((a) => a.id === Number(formValues.assignment_id))
    if (!assignment || !formValues.session_date || !formValues.start_time || !formValues.end_time) {
      setFormError('All fields are required.')
      return
    }
    setIsSubmitting(true)
    try {
      const session = await attendanceSessionsApi.create({
        subject_id: assignment.subject_id,
        section_id: assignment.section_id,
        session_date: formValues.session_date,
        start_time: `${formValues.start_time}:00`,
        end_time: `${formValues.end_time}:00`,
      })
      showToast('Session created.', 'success')
      await queryClient.invalidateQueries({ queryKey: ['attendance-sessions'] })
      setIsModalOpen(false)
      navigate(`/faculty/sessions/${session.id}`)
    } catch (err) {
      setFormError(err instanceof ApiError ? err.message : 'Something went wrong. Please try again.')
    } finally {
      setIsSubmitting(false)
    }
  }

  const columns: DataTableColumn<AttendanceSession>[] = [
    { key: 'session_date', label: 'Date' },
    { key: 'start_time', label: 'Time', render: (row) => `${row.start_time.slice(0, 5)} – ${row.end_time.slice(0, 5)}` },
    { key: 'subject_name', label: 'Subject', render: (row) => `${row.subject_name} (${row.subject_code})` },
    { key: 'section_name', label: 'Section' },
    { key: 'status', label: 'Status', render: (row) => <StatusBadge status={row.status} /> },
    {
      key: 'actions',
      label: '',
      align: 'right',
      render: (row) => (
        <Button variant="ghost" className="!px-2 !py-1" onClick={() => navigate(`/faculty/sessions/${row.id}`)}>
          {row.status === 'SUBMITTED' ? 'View' : 'Mark Attendance'}
        </Button>
      ),
    },
  ]

  return (
    <div className="flex flex-col gap-5">
      <PageHeader
        title="Attendance Sessions"
        description="Create sessions and mark attendance for your assigned sections."
        action={
          <Button onClick={openModal} disabled={isLoadingAssignments || assignmentOptions.length === 0}>
            <Plus className="h-4 w-4" strokeWidth={2} />
            New Session
          </Button>
        }
      />

      <div className="overflow-hidden rounded-xl">
        <DataTable
          columns={columns}
          rows={data?.items ?? []}
          rowKey={(row) => row.id}
          isLoading={isLoading}
          error={isError ? error : undefined}
          onRetry={() => void refetch()}
          emptyTitle="No sessions yet"
          emptyDescription="Create your first attendance session to get started."
        />
        {data && data.total > 0 && (
          <Pagination page={data.page} pageSize={data.page_size} total={data.total} onPageChange={setPage} />
        )}
      </div>

      {isModalOpen && (
        <Modal title="New Attendance Session" onClose={() => setIsModalOpen(false)}>
          {isLoadingAssignments ? (
            <LoadingState label="Loading your assignments…" />
          ) : (
            <form
              onSubmit={(event) => {
                event.preventDefault()
                void handleSubmit()
              }}
              className="flex flex-col gap-4"
            >
              <SelectField
                label="Subject / Section"
                required
                value={formValues.assignment_id}
                onChange={(event) => setFormValues((prev) => ({ ...prev, assignment_id: event.target.value }))}
              >
                <option value="" disabled>
                  Select subject and section…
                </option>
                {assignmentOptions.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </SelectField>
              <FormField
                label="Session Date"
                type="date"
                required
                value={formValues.session_date}
                onChange={(event) => setFormValues((prev) => ({ ...prev, session_date: event.target.value }))}
              />
              <div className="grid grid-cols-2 gap-4">
                <FormField
                  label="Start Time"
                  type="time"
                  required
                  value={formValues.start_time}
                  onChange={(event) => setFormValues((prev) => ({ ...prev, start_time: event.target.value }))}
                />
                <FormField
                  label="End Time"
                  type="time"
                  required
                  value={formValues.end_time}
                  onChange={(event) => setFormValues((prev) => ({ ...prev, end_time: event.target.value }))}
                />
              </div>

              {formError && (
                <p role="alert" className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">
                  {formError}
                </p>
              )}

              <div className="mt-2 flex justify-end gap-3">
                <Button type="button" variant="secondary" onClick={() => setIsModalOpen(false)}>
                  Cancel
                </Button>
                <Button type="submit" isLoading={isSubmitting}>
                  Create Session
                </Button>
              </div>
            </form>
          )}
        </Modal>
      )}
    </div>
  )
}
