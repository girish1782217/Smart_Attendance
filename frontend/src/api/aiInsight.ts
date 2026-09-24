import { apiFetch } from './client'
import type { AttendanceCounts, SubjectAttendanceSummary } from './dashboard'

export interface AIInsight {
  student_id: number
  overall: AttendanceCounts
  by_subject: SubjectAttendanceSummary[]
  ai_available: boolean
  insight_text: string | null
  ai_error_code: string | null
}

export const aiInsightApi = {
  get: (studentId: number) => apiFetch<AIInsight>(`/api/v1/students/${studentId}/ai-insight`),
}
