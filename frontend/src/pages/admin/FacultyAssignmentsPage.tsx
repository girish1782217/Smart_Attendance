import { useQuery, useQueryClient } from '@tanstack/react-query'
import { Plus } from 'lucide-react'
import { useState } from 'react'

import { ApiError } from '../../api/client'
import { facultyApi } from '../../api/faculty'
import { facultyAssignmentsApi, type FacultyAssignment } from '../../api/facultyAssignments'
import { sectionsApi } from '../../api/sections'
import { semestersApi } from '../../api/semesters'
import { subjectsApi } from '../../api/subjects'
import { Button } from '../../components/Button'
import { ConfirmDialog } from '../../components/ConfirmDialog'
import { DataTable, type DataTableColumn } from '../../components/DataTable'
import { LoadingState } from '../../components/LoadingState'
import { Modal } from '../../components/Modal'
import { PageHeader } from '../../components/PageHeader'
import { Pagination } from '../../components/Pagination'
import { SelectField } from '../../components/FormField'
import { StatusBadge } from '../../components/StatusBadge'
import { useToast } from '../../contexts/ToastContext'

const EMPTY_FORM = { faculty_id: '', subject_id: '', section_id: '', semester_id: '' }

export function FacultyAssignmentsPage() {
  const queryClient = useQueryClient()
  const { showToast } = useToast()

  const [page, setPage] = useState(1)
  const [facultyFilter, setFacultyFilter] = useState('')
  const [subjectFilter, setSubjectFilter] = useState('')
  const [sectionFilter, setSectionFilter] = useState('')
  const [semesterFilter, setSemesterFilter] = useState('')
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [formValues, setFormValues] = useState(EMPTY_FORM)
  const [formError, setFormError] = useState<string | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [deactivateTarget, setDeactivateTarget] = useState<FacultyAssignment | null>(null)
  const [isDeactivating, setIsDeactivating] = useState(false)

  const { data: faculty, isLoading: isLoadingFaculty } = useQuery({
    queryKey: ['faculty', 'all'],
    queryFn: () => facultyApi.list({ page_size: 100 }),
  })
  const { data: subjects, isLoading: isLoadingSubjects } = useQuery({
    queryKey: ['subjects', 'all'],
    queryFn: () => subjectsApi.list({ page_size: 100 }),
  })
  const { data: sections, isLoading: isLoadingSections } = useQuery({
    queryKey: ['sections', 'all'],
    queryFn: () => sectionsApi.list({ page_size: 100 }),
  })
  const { data: semesters, isLoading: isLoadingSemesters } = useQuery({
    queryKey: ['semesters', 'all'],
    queryFn: () => semestersApi.list({ page_size: 100 }),
  })

  const isLoadingOptions = isLoadingFaculty || isLoadingSubjects || isLoadingSections || isLoadingSemesters

  const facultyNameById = new Map((faculty?.items ?? []).map((item) => [item.id, item.full_name]))
  const subjectNameById = new Map((subjects?.items ?? []).map((item) => [item.id, `${item.name} (${item.code})`]))
  const sectionNameById = new Map((sections?.items ?? []).map((item) => [item.id, item.name]))
  const semesterNameById = new Map((semesters?.items ?? []).map((item) => [item.id, item.name]))

  const queryParams: Record<string, unknown> = {
    page,
    page_size: 10,
    faculty_id: facultyFilter || undefined,
    subject_id: subjectFilter || undefined,
    section_id: sectionFilter || undefined,
    semester_id: semesterFilter || undefined,
  }

  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: ['faculty-assignments', page, facultyFilter, subjectFilter, sectionFilter, semesterFilter],
    queryFn: () => facultyAssignmentsApi.list(queryParams),
    enabled: !isLoadingOptions,
  })

  if (isLoadingOptions) return <LoadingState label="Loading assignment options…" />

  function openModal() {
    setFormValues(EMPTY_FORM)
    setFormError(null)
    setIsModalOpen(true)
  }

  async function handleSubmit() {
    setFormError(null)
    if (!formValues.faculty_id || !formValues.subject_id || !formValues.section_id || !formValues.semester_id) {
      setFormError('All fields are required.')
      return
    }
    setIsSubmitting(true)
    try {
      await facultyAssignmentsApi.create({
        faculty_id: Number(formValues.faculty_id),
        subject_id: Number(formValues.subject_id),
        section_id: Number(formValues.section_id),
        semester_id: Number(formValues.semester_id),
      })
      showToast('Assignment created.', 'success')
      await queryClient.invalidateQueries({ queryKey: ['faculty-assignments'] })
      setIsModalOpen(false)
    } catch (err) {
      setFormError(err instanceof ApiError ? err.message : 'Something went wrong. Please try again.')
    } finally {
      setIsSubmitting(false)
    }
  }

  async function handleConfirmDeactivate() {
    if (!deactivateTarget) return
    setIsDeactivating(true)
    try {
      await facultyAssignmentsApi.deactivate(deactivateTarget.id)
      showToast('Assignment deactivated.', 'success')
      await queryClient.invalidateQueries({ queryKey: ['faculty-assignments'] })
      setDeactivateTarget(null)
    } catch (err) {
      showToast(err instanceof ApiError ? err.message : 'Something went wrong. Please try again.', 'error')
    } finally {
      setIsDeactivating(false)
    }
  }

  const columns: DataTableColumn<FacultyAssignment>[] = [
    { key: 'faculty_id', label: 'Faculty', render: (row) => facultyNameById.get(row.faculty_id) ?? '—' },
    { key: 'subject_id', label: 'Subject', render: (row) => subjectNameById.get(row.subject_id) ?? '—' },
    { key: 'section_id', label: 'Section', render: (row) => sectionNameById.get(row.section_id) ?? '—' },
    { key: 'semester_id', label: 'Semester', render: (row) => semesterNameById.get(row.semester_id) ?? '—' },
    { key: 'is_active', label: 'Status', render: (row) => <StatusBadge status={row.is_active ? 'ACTIVE' : 'INACTIVE'} /> },
    {
      key: 'actions',
      label: '',
      align: 'right',
      render: (row) =>
        row.is_active ? (
          <Button
            variant="ghost"
            className="!px-2 !py-1 text-red-600 hover:bg-red-50 hover:text-red-700"
            onClick={() => setDeactivateTarget(row)}
          >
            Deactivate
          </Button>
        ) : (
          <span className="text-xs text-slate-400">Re-create to reactivate</span>
        ),
    },
  ]

  return (
    <div className="flex flex-col gap-5">
      <PageHeader
        title="Faculty Assignments"
        description="Assign faculty to teach a subject for a section during a semester."
        action={
          <Button onClick={openModal}>
            <Plus className="h-4 w-4" strokeWidth={2} />
            Add Assignment
          </Button>
        }
      />

      <div className="flex flex-wrap gap-3">
        <FilterSelect
          label="All Faculty"
          value={facultyFilter}
          onChange={(value) => {
            setFacultyFilter(value)
            setPage(1)
          }}
          options={faculty?.items.map((f) => ({ value: f.id, label: f.full_name })) ?? []}
        />
        <FilterSelect
          label="All Subjects"
          value={subjectFilter}
          onChange={(value) => {
            setSubjectFilter(value)
            setPage(1)
          }}
          options={subjects?.items.map((s) => ({ value: s.id, label: `${s.name} (${s.code})` })) ?? []}
        />
        <FilterSelect
          label="All Sections"
          value={sectionFilter}
          onChange={(value) => {
            setSectionFilter(value)
            setPage(1)
          }}
          options={sections?.items.map((s) => ({ value: s.id, label: s.name })) ?? []}
        />
        <FilterSelect
          label="All Semesters"
          value={semesterFilter}
          onChange={(value) => {
            setSemesterFilter(value)
            setPage(1)
          }}
          options={semesters?.items.map((s) => ({ value: s.id, label: s.name })) ?? []}
        />
      </div>

      <div className="overflow-hidden rounded-xl">
        <DataTable
          columns={columns}
          rows={data?.items ?? []}
          rowKey={(row) => row.id}
          isLoading={isLoading}
          error={isError ? error : undefined}
          onRetry={() => void refetch()}
          emptyTitle="No assignments found"
          emptyDescription="Add the first assignment to get started."
        />
        {data && data.total > 0 && (
          <Pagination page={data.page} pageSize={data.page_size} total={data.total} onPageChange={setPage} />
        )}
      </div>

      {isModalOpen && (
        <Modal title="Add Assignment" onClose={() => setIsModalOpen(false)}>
          <form
            onSubmit={(event) => {
              event.preventDefault()
              void handleSubmit()
            }}
            className="flex flex-col gap-4"
          >
            <SelectField
              label="Faculty"
              required
              value={formValues.faculty_id}
              onChange={(event) => setFormValues((prev) => ({ ...prev, faculty_id: event.target.value }))}
            >
              <option value="" disabled>
                Select faculty…
              </option>
              {faculty?.items.map((item) => (
                <option key={item.id} value={item.id}>
                  {item.full_name}
                </option>
              ))}
            </SelectField>
            <SelectField
              label="Subject"
              required
              value={formValues.subject_id}
              onChange={(event) => setFormValues((prev) => ({ ...prev, subject_id: event.target.value }))}
            >
              <option value="" disabled>
                Select subject…
              </option>
              {subjects?.items.map((item) => (
                <option key={item.id} value={item.id}>
                  {item.name} ({item.code})
                </option>
              ))}
            </SelectField>
            <SelectField
              label="Section"
              required
              value={formValues.section_id}
              onChange={(event) => setFormValues((prev) => ({ ...prev, section_id: event.target.value }))}
            >
              <option value="" disabled>
                Select section…
              </option>
              {sections?.items.map((item) => (
                <option key={item.id} value={item.id}>
                  {item.name}
                </option>
              ))}
            </SelectField>
            <SelectField
              label="Semester"
              required
              value={formValues.semester_id}
              onChange={(event) => setFormValues((prev) => ({ ...prev, semester_id: event.target.value }))}
            >
              <option value="" disabled>
                Select semester…
              </option>
              {semesters?.items.map((item) => (
                <option key={item.id} value={item.id}>
                  {item.name}
                </option>
              ))}
            </SelectField>

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
                Create Assignment
              </Button>
            </div>
          </form>
        </Modal>
      )}

      {deactivateTarget && (
        <ConfirmDialog
          title="Deactivate Assignment"
          message="This will deactivate the selected assignment. Continue?"
          confirmLabel="Deactivate"
          danger
          isSubmitting={isDeactivating}
          onConfirm={() => void handleConfirmDeactivate()}
          onCancel={() => setDeactivateTarget(null)}
        />
      )}
    </div>
  )
}

function FilterSelect({
  label,
  value,
  onChange,
  options,
}: {
  label: string
  value: string
  onChange: (value: string) => void
  options: { value: number; label: string }[]
}) {
  return (
    <select
      value={value}
      onChange={(event) => onChange(event.target.value)}
      className="rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 shadow-sm focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/20"
    >
      <option value="">{label}</option>
      {options.map((option) => (
        <option key={option.value} value={option.value}>
          {option.label}
        </option>
      ))}
    </select>
  )
}
