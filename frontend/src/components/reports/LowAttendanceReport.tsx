import { useQuery } from '@tanstack/react-query'
import { Download } from 'lucide-react'
import { useState } from 'react'

import { academicClassesApi } from '../../api/academicClasses'
import { ApiError } from '../../api/client'
import { departmentsApi } from '../../api/departments'
import { reportsApi } from '../../api/reports'
import { sectionsApi } from '../../api/sections'
import { subjectsApi } from '../../api/subjects'
import { useToast } from '../../contexts/ToastContext'
import { downloadBlob } from '../../utils/downloadBlob'
import { Button } from '../Button'
import { DataTable, type DataTableColumn } from '../DataTable'
import { Pagination } from '../Pagination'
import { SearchInput } from '../SearchInput'

export function useFilterOptions() {
  const { data: departments } = useQuery({ queryKey: ['departments', 'all'], queryFn: () => departmentsApi.list({ page_size: 100 }) })
  const { data: classes } = useQuery({ queryKey: ['classes', 'all'], queryFn: () => academicClassesApi.list({ page_size: 100 }) })
  const { data: sections } = useQuery({ queryKey: ['sections', 'all'], queryFn: () => sectionsApi.list({ page_size: 100 }) })
  const { data: subjects } = useQuery({ queryKey: ['subjects', 'all'], queryFn: () => subjectsApi.list({ page_size: 100 }) })
  return {
    departmentOptions: (departments?.items ?? []).map((d) => ({ value: d.id, label: d.name })),
    classOptions: (classes?.items ?? []).map((c) => ({ value: c.id, label: c.name })),
    sectionOptions: (sections?.items ?? []).map((s) => ({ value: s.id, label: s.name })),
    subjectOptions: (subjects?.items ?? []).map((s) => ({ value: s.id, label: `${s.name} (${s.code})` })),
  }
}

export function FilterSelect({
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

export function ExportButton({ onExport }: { onExport: () => Promise<void> }) {
  const [isExporting, setIsExporting] = useState(false)
  const { showToast } = useToast()
  return (
    <Button
      variant="secondary"
      isLoading={isExporting}
      onClick={() => {
        setIsExporting(true)
        onExport()
          .catch((err) => showToast(err instanceof ApiError ? err.message : 'Export failed. Please try again.', 'error'))
          .finally(() => setIsExporting(false))
      }}
    >
      <Download className="h-4 w-4" strokeWidth={2} />
      Export CSV
    </Button>
  )
}

/** Shared by the Admin Reports page's "Low Attendance" tab and the
 * Faculty "Low Attendance" page -- the backend does not scope this report
 * to the calling faculty's own sections (only faculty-activity is scoped),
 * so both roles see the same data through the same UI. */
export function LowAttendanceReport() {
  const { departmentOptions, classOptions, sectionOptions, subjectOptions } = useFilterOptions()
  const [bySubject, setBySubject] = useState(false)
  const [page, setPage] = useState(1)
  const [search, setSearch] = useState('')
  const [departmentId, setDepartmentId] = useState('')
  const [classId, setClassId] = useState('')
  const [sectionId, setSectionId] = useState('')
  const [subjectId, setSubjectId] = useState('')
  const [threshold, setThreshold] = useState('')

  const filters: Record<string, unknown> = {
    page,
    page_size: 10,
    search: search || undefined,
    department_id: departmentId || undefined,
    class_id: classId || undefined,
    section_id: sectionId || undefined,
    threshold: threshold || undefined,
  }
  if (bySubject) filters.subject_id = subjectId || undefined

  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: ['reports', 'low-attendance', bySubject, filters],
    queryFn: () => (bySubject ? reportsApi.lowAttendanceBySubject(filters) : reportsApi.lowAttendanceOverall(filters)),
  })

  const exportParams: Record<string, unknown> = { ...filters }
  delete exportParams.page
  delete exportParams.page_size

  const columns: DataTableColumn<Record<string, unknown>>[] = [
    { key: 'roll_number', label: 'Roll Number' },
    { key: 'student_name', label: 'Student' },
    ...(bySubject
      ? [{ key: 'subject_name', label: 'Subject', render: (row: Record<string, unknown>) => `${row.subject_name} (${row.subject_code})` }]
      : []),
    { key: 'present_count', label: 'Present', align: 'right' as const },
    { key: 'absent_count', label: 'Absent', align: 'right' as const },
    { key: 'late_count', label: 'Late', align: 'right' as const },
    { key: 'excused_count', label: 'Excused', align: 'right' as const },
    { key: 'percentage', label: 'Percentage', align: 'right' as const, render: (row: Record<string, unknown>) => `${row.percentage}%` },
  ]

  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-wrap items-center gap-3">
        <SearchInput value={search} onChange={(v) => { setSearch(v); setPage(1) }} placeholder="Search students…" />
        <FilterSelect label="All Departments" value={departmentId} onChange={(v) => { setDepartmentId(v); setPage(1) }} options={departmentOptions} />
        <FilterSelect label="All Classes" value={classId} onChange={(v) => { setClassId(v); setPage(1) }} options={classOptions} />
        <FilterSelect label="All Sections" value={sectionId} onChange={(v) => { setSectionId(v); setPage(1) }} options={sectionOptions} />
        {bySubject && (
          <FilterSelect label="All Subjects" value={subjectId} onChange={(v) => { setSubjectId(v); setPage(1) }} options={subjectOptions} />
        )}
        <input
          type="number"
          min={1}
          max={100}
          step="0.1"
          value={threshold}
          onChange={(event) => { setThreshold(event.target.value); setPage(1) }}
          placeholder={data ? `Threshold: ${data.threshold}%` : 'Threshold %'}
          className="w-36 rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 shadow-sm focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/20"
        />
        <label className="flex items-center gap-2 text-sm text-slate-600">
          <input
            type="checkbox"
            checked={bySubject}
            onChange={(event) => { setBySubject(event.target.checked); setPage(1) }}
            className="h-4 w-4 rounded border-slate-300 text-brand-600 focus:ring-brand-500/40"
          />
          Group by subject
        </label>
        <div className="ml-auto">
          <ExportButton
            onExport={async () => {
              const blob = bySubject
                ? await reportsApi.exportLowAttendanceBySubject(exportParams)
                : await reportsApi.exportLowAttendanceOverall(exportParams)
              downloadBlob(blob, bySubject ? 'low_attendance_by_subject.csv' : 'low_attendance_overall.csv')
            }}
          />
        </div>
      </div>

      <div className="overflow-hidden rounded-xl">
        <DataTable
          columns={columns}
          rows={(data?.items as unknown as Record<string, unknown>[]) ?? []}
          rowKey={(row) => `${row.student_id}-${row.subject_id ?? ''}`}
          isLoading={isLoading}
          error={isError ? error : undefined}
          onRetry={() => void refetch()}
          emptyTitle="No students below threshold"
        />
        {data && data.total > 0 && (
          <Pagination page={data.page} pageSize={data.page_size} total={data.total} onPageChange={setPage} />
        )}
      </div>
    </div>
  )
}
