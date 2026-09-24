import { useQuery } from '@tanstack/react-query'
import { useState } from 'react'

import { ApiError } from '../../api/client'
import { facultyApi } from '../../api/faculty'
import { reportsApi, type LowAttendanceBySubjectRow, type LowAttendanceOverallRow } from '../../api/reports'
import { DataTable, type DataTableColumn } from '../../components/DataTable'
import { PageHeader } from '../../components/PageHeader'
import { Pagination } from '../../components/Pagination'
import { ExportButton, FilterSelect, LowAttendanceReport, useFilterOptions } from '../../components/reports/LowAttendanceReport'
import { SearchInput } from '../../components/SearchInput'
import { downloadBlob } from '../../utils/downloadBlob'

type Tab = 'low-attendance' | 'student-attendance' | 'subject-attendance' | 'faculty-activity'

const TABS: { value: Tab; label: string }[] = [
  { value: 'low-attendance', label: 'Low Attendance' },
  { value: 'student-attendance', label: 'Student Attendance' },
  { value: 'subject-attendance', label: 'Subject Attendance' },
  { value: 'faculty-activity', label: 'Faculty Activity' },
]

function StudentAttendanceTab() {
  const { departmentOptions, classOptions, sectionOptions } = useFilterOptions()
  const [page, setPage] = useState(1)
  const [search, setSearch] = useState('')
  const [departmentId, setDepartmentId] = useState('')
  const [classId, setClassId] = useState('')
  const [sectionId, setSectionId] = useState('')
  const [fromDate, setFromDate] = useState('')
  const [toDate, setToDate] = useState('')

  const filters: Record<string, unknown> = {
    page,
    page_size: 10,
    search: search || undefined,
    department_id: departmentId || undefined,
    class_id: classId || undefined,
    section_id: sectionId || undefined,
    from_date: fromDate || undefined,
    to_date: toDate || undefined,
  }

  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: ['reports', 'student-attendance', filters],
    queryFn: () => reportsApi.studentAttendance(filters),
  })

  const exportParams: Record<string, unknown> = { ...filters }
  delete exportParams.page
  delete exportParams.page_size

  const columns: DataTableColumn<LowAttendanceOverallRow>[] = [
    { key: 'roll_number', label: 'Roll Number' },
    { key: 'student_name', label: 'Student' },
    { key: 'present_count', label: 'Present', align: 'right' },
    { key: 'absent_count', label: 'Absent', align: 'right' },
    { key: 'late_count', label: 'Late', align: 'right' },
    { key: 'excused_count', label: 'Excused', align: 'right' },
    { key: 'percentage', label: 'Percentage', align: 'right', render: (row) => `${row.percentage}%` },
  ]

  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-wrap items-center gap-3">
        <SearchInput value={search} onChange={(v) => { setSearch(v); setPage(1) }} placeholder="Search students…" />
        <FilterSelect label="All Departments" value={departmentId} onChange={(v) => { setDepartmentId(v); setPage(1) }} options={departmentOptions} />
        <FilterSelect label="All Classes" value={classId} onChange={(v) => { setClassId(v); setPage(1) }} options={classOptions} />
        <FilterSelect label="All Sections" value={sectionId} onChange={(v) => { setSectionId(v); setPage(1) }} options={sectionOptions} />
        <input type="date" value={fromDate} onChange={(e) => { setFromDate(e.target.value); setPage(1) }} className="rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 shadow-sm focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/20" />
        <input type="date" value={toDate} onChange={(e) => { setToDate(e.target.value); setPage(1) }} className="rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 shadow-sm focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/20" />
        <div className="ml-auto">
          <ExportButton
            onExport={async () => {
              const blob = await reportsApi.exportStudentAttendance(exportParams)
              downloadBlob(blob, 'student_attendance_report.csv')
            }}
          />
        </div>
      </div>

      <div className="overflow-hidden rounded-xl">
        <DataTable
          columns={columns}
          rows={data?.items ?? []}
          rowKey={(row) => row.student_id}
          isLoading={isLoading}
          error={isError ? error : undefined}
          onRetry={() => void refetch()}
          emptyTitle="No records found"
        />
        {data && data.total > 0 && (
          <Pagination page={data.page} pageSize={data.page_size} total={data.total} onPageChange={setPage} />
        )}
      </div>
    </div>
  )
}

function SubjectAttendanceTab() {
  const { departmentOptions, classOptions, sectionOptions, subjectOptions } = useFilterOptions()
  const [page, setPage] = useState(1)
  const [search, setSearch] = useState('')
  const [departmentId, setDepartmentId] = useState('')
  const [classId, setClassId] = useState('')
  const [sectionId, setSectionId] = useState('')
  const [subjectId, setSubjectId] = useState('')
  const [fromDate, setFromDate] = useState('')
  const [toDate, setToDate] = useState('')

  const filters: Record<string, unknown> = {
    page,
    page_size: 10,
    search: search || undefined,
    department_id: departmentId || undefined,
    class_id: classId || undefined,
    section_id: sectionId || undefined,
    subject_id: subjectId || undefined,
    from_date: fromDate || undefined,
    to_date: toDate || undefined,
  }

  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: ['reports', 'subject-attendance', filters],
    queryFn: () => reportsApi.subjectAttendance(filters),
  })

  const exportParams: Record<string, unknown> = { ...filters }
  delete exportParams.page
  delete exportParams.page_size

  const columns: DataTableColumn<LowAttendanceBySubjectRow>[] = [
    { key: 'roll_number', label: 'Roll Number' },
    { key: 'student_name', label: 'Student' },
    { key: 'subject_name', label: 'Subject', render: (row) => `${row.subject_name} (${row.subject_code})` },
    { key: 'present_count', label: 'Present', align: 'right' },
    { key: 'absent_count', label: 'Absent', align: 'right' },
    { key: 'late_count', label: 'Late', align: 'right' },
    { key: 'excused_count', label: 'Excused', align: 'right' },
    { key: 'percentage', label: 'Percentage', align: 'right', render: (row) => `${row.percentage}%` },
  ]

  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-wrap items-center gap-3">
        <SearchInput value={search} onChange={(v) => { setSearch(v); setPage(1) }} placeholder="Search students…" />
        <FilterSelect label="All Departments" value={departmentId} onChange={(v) => { setDepartmentId(v); setPage(1) }} options={departmentOptions} />
        <FilterSelect label="All Classes" value={classId} onChange={(v) => { setClassId(v); setPage(1) }} options={classOptions} />
        <FilterSelect label="All Sections" value={sectionId} onChange={(v) => { setSectionId(v); setPage(1) }} options={sectionOptions} />
        <FilterSelect label="All Subjects" value={subjectId} onChange={(v) => { setSubjectId(v); setPage(1) }} options={subjectOptions} />
        <input type="date" value={fromDate} onChange={(e) => { setFromDate(e.target.value); setPage(1) }} className="rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 shadow-sm focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/20" />
        <input type="date" value={toDate} onChange={(e) => { setToDate(e.target.value); setPage(1) }} className="rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 shadow-sm focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/20" />
        <div className="ml-auto">
          <ExportButton
            onExport={async () => {
              const blob = await reportsApi.exportSubjectAttendance(exportParams)
              downloadBlob(blob, 'subject_attendance_report.csv')
            }}
          />
        </div>
      </div>

      <div className="overflow-hidden rounded-xl">
        <DataTable
          columns={columns}
          rows={data?.items ?? []}
          rowKey={(row) => `${row.student_id}-${row.subject_id}`}
          isLoading={isLoading}
          error={isError ? error : undefined}
          onRetry={() => void refetch()}
          emptyTitle="No records found"
        />
        {data && data.total > 0 && (
          <Pagination page={data.page} pageSize={data.page_size} total={data.total} onPageChange={setPage} />
        )}
      </div>
    </div>
  )
}

function FacultyActivityTab() {
  const [facultyId, setFacultyId] = useState('')
  const [fromDate, setFromDate] = useState('')
  const [toDate, setToDate] = useState('')

  const { data: faculty } = useQuery({ queryKey: ['faculty', 'all'], queryFn: () => facultyApi.list({ page_size: 100 }) })

  const { data, isLoading, isError, error } = useQuery({
    queryKey: ['reports', 'faculty-activity', facultyId, fromDate, toDate],
    queryFn: () =>
      reportsApi.facultyActivity({ faculty_id: facultyId, from_date: fromDate || undefined, to_date: toDate || undefined }),
    enabled: Boolean(facultyId),
  })

  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-wrap items-center gap-3">
        <FilterSelect
          label="Select faculty…"
          value={facultyId}
          onChange={setFacultyId}
          options={(faculty?.items ?? []).map((f) => ({ value: f.id, label: f.full_name }))}
        />
        <input type="date" value={fromDate} onChange={(e) => setFromDate(e.target.value)} className="rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 shadow-sm focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/20" />
        <input type="date" value={toDate} onChange={(e) => setToDate(e.target.value)} className="rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 shadow-sm focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/20" />
      </div>

      {!facultyId && <p className="text-sm text-slate-500">Select a faculty member to view their activity.</p>}
      {facultyId && isLoading && <p className="text-sm text-slate-500">Loading…</p>}
      {facultyId && isError && (
        <p className="text-sm text-red-600">{error instanceof ApiError ? error.message : 'Something went wrong.'}</p>
      )}
      {data && (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
          <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
            <p className="text-xs font-medium uppercase tracking-wide text-slate-500">Total Sessions</p>
            <p className="mt-2 text-2xl font-semibold text-slate-900">{data.total_sessions}</p>
          </div>
          <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
            <p className="text-xs font-medium uppercase tracking-wide text-slate-500">Submitted</p>
            <p className="mt-2 text-2xl font-semibold text-emerald-700">{data.submitted_sessions}</p>
          </div>
          <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
            <p className="text-xs font-medium uppercase tracking-wide text-slate-500">Scheduled</p>
            <p className="mt-2 text-2xl font-semibold text-amber-700">{data.scheduled_sessions}</p>
          </div>
        </div>
      )}
    </div>
  )
}

export function ReportsPage() {
  const [tab, setTab] = useState<Tab>('low-attendance')

  return (
    <div className="flex flex-col gap-5">
      <PageHeader title="Reports" description="Generate attendance reports and export them as CSV." />

      <div className="flex gap-1 border-b border-slate-200">
        {TABS.map((t) => (
          <button
            key={t.value}
            type="button"
            onClick={() => setTab(t.value)}
            className={`border-b-2 px-3 py-2 text-sm font-medium transition ${
              tab === t.value
                ? 'border-brand-600 text-brand-700'
                : 'border-transparent text-slate-500 hover:text-slate-700'
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      {tab === 'low-attendance' && <LowAttendanceReport />}
      {tab === 'student-attendance' && <StudentAttendanceTab />}
      {tab === 'subject-attendance' && <SubjectAttendanceTab />}
      {tab === 'faculty-activity' && <FacultyActivityTab />}
    </div>
  )
}
