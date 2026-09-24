import { apiFetch, buildQueryString } from './client'
import type { Page } from '../types/pagination'

export type AttendanceStatus = 'PRESENT' | 'ABSENT' | 'LATE' | 'EXCUSED'
export type AttendanceSessionStatus = 'SCHEDULED' | 'SUBMITTED'

export interface AttendanceSession {
  id: number
  faculty_id: number
  faculty_name: string
  subject_id: number
  subject_name: string
  subject_code: string
  section_id: number
  section_name: string
  session_date: string
  start_time: string
  end_time: string
  status: AttendanceSessionStatus
  created_at: string
  updated_at: string
}

export interface AttendanceSessionCreate {
  faculty_id?: number | null
  subject_id: number
  section_id: number
  session_date: string
  start_time: string
  end_time: string
}

export interface AttendanceRecord {
  id: number
  session_id: number
  student_id: number
  roll_number: string
  student_name: string
  status: AttendanceStatus
  recorded_by_user_id: number
  recorded_at: string
}

export const attendanceSessionsApi = {
  list: (params: Record<string, unknown> = {}) =>
    apiFetch<Page<AttendanceSession>>(`/api/v1/attendance-sessions${buildQueryString(params)}`),
  get: (id: number) => apiFetch<AttendanceSession>(`/api/v1/attendance-sessions/${id}`),
  create: (payload: AttendanceSessionCreate) =>
    apiFetch<AttendanceSession>('/api/v1/attendance-sessions', { method: 'POST', body: JSON.stringify(payload) }),
  getRoster: (id: number) => apiFetch<{ id: number; roll_number: string; full_name: string }[]>(
    `/api/v1/attendance-sessions/${id}/roster`,
  ),
  getRecords: (id: number) => apiFetch<AttendanceRecord[]>(`/api/v1/attendance-sessions/${id}/records`),
  markRecords: (id: number, records: { student_id: number; status: AttendanceStatus }[]) =>
    apiFetch<AttendanceRecord[]>(`/api/v1/attendance-sessions/${id}/records`, {
      method: 'PUT',
      body: JSON.stringify({ records }),
    }),
  submit: (id: number) => apiFetch<AttendanceSession>(`/api/v1/attendance-sessions/${id}/submit`, { method: 'POST' }),
}
