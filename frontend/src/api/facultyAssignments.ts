import { apiFetch, buildQueryString } from './client'
import type { Page } from '../types/pagination'

export interface FacultyAssignment {
  id: number
  faculty_id: number
  subject_id: number
  section_id: number
  semester_id: number
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface FacultyAssignmentCreate {
  faculty_id: number
  subject_id: number
  section_id: number
  semester_id: number
}

// No PATCH/update endpoint exists for this resource -- only create/list/get/deactivate.
// Re-creating the same (faculty, subject, section, semester) combo after a
// deactivate is how the backend supports "reactivating" one (SPEC06).
export const facultyAssignmentsApi = {
  list: (params: Record<string, unknown> = {}) =>
    apiFetch<Page<FacultyAssignment>>(`/api/v1/faculty-assignments${buildQueryString(params)}`),
  create: (payload: FacultyAssignmentCreate) =>
    apiFetch<FacultyAssignment>('/api/v1/faculty-assignments', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),
  deactivate: (id: number) =>
    apiFetch<FacultyAssignment>(`/api/v1/faculty-assignments/${id}`, { method: 'DELETE' }),
}
