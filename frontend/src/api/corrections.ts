import { apiFetch, buildQueryString } from './client'
import type { AttendanceStatus } from './attendanceSessions'
import type { Page } from '../types/pagination'

export type CorrectionRequestStatus = 'PENDING' | 'APPROVED' | 'REJECTED'

export interface Correction {
  id: number
  attendance_record_id: number
  student_id: number
  student_name: string
  session_id: number
  original_status: AttendanceStatus
  requested_status: AttendanceStatus
  reason: string
  requested_by_user_id: number
  requested_by_name: string
  requested_at: string
  status: CorrectionRequestStatus
  reviewed_by_user_id: number | null
  reviewed_by_name: string | null
  reviewed_at: string | null
  decision_reason: string | null
}

export interface CorrectionCreate {
  requested_status: AttendanceStatus
  reason: string
}

export const correctionsApi = {
  list: (params: Record<string, unknown> = {}) =>
    apiFetch<Page<Correction>>(`/api/v1/corrections${buildQueryString(params)}`),
  approve: (id: number, decisionReason?: string) =>
    apiFetch<Correction>(`/api/v1/corrections/${id}/approve`, {
      method: 'POST',
      body: JSON.stringify({ decision_reason: decisionReason || null }),
    }),
  reject: (id: number, decisionReason?: string) =>
    apiFetch<Correction>(`/api/v1/corrections/${id}/reject`, {
      method: 'POST',
      body: JSON.stringify({ decision_reason: decisionReason || null }),
    }),
  create: (attendanceRecordId: number, payload: CorrectionCreate) =>
    apiFetch<Correction>(`/api/v1/attendance-records/${attendanceRecordId}/corrections`, {
      method: 'POST',
      body: JSON.stringify(payload),
    }),
}
