import { apiFetch, buildQueryString } from './client'
import type { AttendanceCounts, AttendanceHistoryRecord, SubjectAttendanceSummary } from './dashboard'
import type { Page } from '../types/pagination'

export interface StudentAttendanceSummary {
  student_id: number
  overall: AttendanceCounts
  by_subject: SubjectAttendanceSummary[]
}

export const attendanceHistoryApi = {
  getSummary: (studentId: number) =>
    apiFetch<StudentAttendanceSummary>(`/api/v1/students/${studentId}/attendance-summary`),
  getHistory: (studentId: number, params: Record<string, unknown> = {}) =>
    apiFetch<Page<AttendanceHistoryRecord>>(
      `/api/v1/students/${studentId}/attendance-history${buildQueryString(params)}`,
    ),
}
