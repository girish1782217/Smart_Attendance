import { apiFetch, apiFetchBlob, buildQueryString } from './client'

export interface LowAttendanceOverallRow {
  student_id: number
  roll_number: string
  student_name: string
  present_count: number
  absent_count: number
  late_count: number
  excused_count: number
  total_applicable: number
  percentage: number
}

export interface LowAttendanceBySubjectRow extends LowAttendanceOverallRow {
  subject_id: number
  subject_name: string
  subject_code: string
}

export interface LowAttendanceOverallReportResponse {
  items: LowAttendanceOverallRow[]
  total: number
  page: number
  page_size: number
  threshold: number
}

export interface LowAttendanceBySubjectReportResponse {
  items: LowAttendanceBySubjectRow[]
  total: number
  page: number
  page_size: number
  threshold: number
}

export interface StudentAttendanceReportResponse {
  items: LowAttendanceOverallRow[]
  total: number
  page: number
  page_size: number
}

export interface SubjectAttendanceReportResponse {
  items: LowAttendanceBySubjectRow[]
  total: number
  page: number
  page_size: number
}

export interface FacultyActivityReportResponse {
  faculty_id: number
  total_sessions: number
  submitted_sessions: number
  scheduled_sessions: number
  from_date: string | null
  to_date: string | null
}

export const reportsApi = {
  lowAttendanceOverall: (params: Record<string, unknown>) =>
    apiFetch<LowAttendanceOverallReportResponse>(`/api/v1/reports/low-attendance/overall${buildQueryString(params)}`),
  lowAttendanceBySubject: (params: Record<string, unknown>) =>
    apiFetch<LowAttendanceBySubjectReportResponse>(
      `/api/v1/reports/low-attendance/by-subject${buildQueryString(params)}`,
    ),
  exportLowAttendanceOverall: (params: Record<string, unknown>) =>
    apiFetchBlob(`/api/v1/reports/low-attendance/overall/export${buildQueryString(params)}`),
  exportLowAttendanceBySubject: (params: Record<string, unknown>) =>
    apiFetchBlob(`/api/v1/reports/low-attendance/by-subject/export${buildQueryString(params)}`),
  studentAttendance: (params: Record<string, unknown>) =>
    apiFetch<StudentAttendanceReportResponse>(`/api/v1/reports/student-attendance${buildQueryString(params)}`),
  exportStudentAttendance: (params: Record<string, unknown>) =>
    apiFetchBlob(`/api/v1/reports/student-attendance/export${buildQueryString(params)}`),
  subjectAttendance: (params: Record<string, unknown>) =>
    apiFetch<SubjectAttendanceReportResponse>(`/api/v1/reports/subject-attendance${buildQueryString(params)}`),
  exportSubjectAttendance: (params: Record<string, unknown>) =>
    apiFetchBlob(`/api/v1/reports/subject-attendance/export${buildQueryString(params)}`),
  facultyActivity: (params: Record<string, unknown>) =>
    apiFetch<FacultyActivityReportResponse>(`/api/v1/reports/faculty-activity${buildQueryString(params)}`),
}
