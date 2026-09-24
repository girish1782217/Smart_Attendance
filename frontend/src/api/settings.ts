import { apiFetch } from './client'

export interface LowAttendanceThreshold {
  threshold: number
}

export const settingsApi = {
  getThreshold: () => apiFetch<LowAttendanceThreshold>('/api/v1/settings/low-attendance-threshold'),
  setThreshold: (threshold: number) =>
    apiFetch<LowAttendanceThreshold>('/api/v1/settings/low-attendance-threshold', {
      method: 'PUT',
      body: JSON.stringify({ threshold }),
    }),
}
