import { apiFetch } from './client'

export interface AdminDashboard {
  total_students: number
  total_faculty: number
  total_departments: number
  total_classes: number
  today_sessions_total: number
  today_sessions_submitted: number
  overall_attendance_percentage: number | null
  students_below_threshold: number
  pending_correction_requests: number
}

export interface FacultyDashboard {
  assigned_sections: number
  today_sessions: number
  total_sessions: number
  students_below_threshold: number
  pending_correction_requests: number
}

export interface AttendanceCounts {
  present_count: number
  absent_count: number
  late_count: number
  excused_count: number
  percentage: number | null
}

export interface SubjectAttendanceSummary extends AttendanceCounts {
  subject_id: number
  subject_name: string
  subject_code: string
}

export interface AttendanceHistoryRecord {
  id: number
  session_id: number
  session_date: string
  start_time: string
  end_time: string
  subject_id: number
  subject_name: string
  subject_code: string
  status: string
  was_corrected: boolean
  correction: {
    original_status: string
    approved_status: string
    reason: string
    decision_reason: string | null
    reviewed_by_name: string | null
    reviewed_at: string | null
  } | null
}

export interface StudentDashboard {
  overall: AttendanceCounts
  by_subject: SubjectAttendanceSummary[]
  recent_attendance: AttendanceHistoryRecord[]
  is_low_attendance: boolean
  threshold: number
  pending_correction_requests: number
}

export function getAdminDashboard(): Promise<AdminDashboard> {
  return apiFetch<AdminDashboard>('/api/v1/dashboard/admin')
}

export function getFacultyDashboard(): Promise<FacultyDashboard> {
  return apiFetch<FacultyDashboard>('/api/v1/dashboard/faculty')
}

export function getStudentDashboard(): Promise<StudentDashboard> {
  return apiFetch<StudentDashboard>('/api/v1/dashboard/student')
}
