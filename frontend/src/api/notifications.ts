import { apiFetch, buildQueryString } from './client'
import type { Page } from '../types/pagination'

export type NotificationType =
  | 'CORRECTION_REQUESTED'
  | 'CORRECTION_APPROVED'
  | 'CORRECTION_REJECTED'
  | 'LOW_ATTENDANCE_WARNING'

export interface Notification {
  id: number
  type: NotificationType
  title: string
  message: string
  related_entity_type: string | null
  related_entity_id: number | null
  is_read: boolean
  created_at: string
  read_at: string | null
}

export const notificationsApi = {
  list: (params: Record<string, unknown> = {}) =>
    apiFetch<Page<Notification>>(`/api/v1/notifications${buildQueryString(params)}`),
  getUnreadCount: () => apiFetch<{ count: number }>('/api/v1/notifications/unread-count'),
  markRead: (id: number) => apiFetch<Notification>(`/api/v1/notifications/${id}/read`, { method: 'POST' }),
  markAllRead: () => apiFetch<{ marked_count: number }>('/api/v1/notifications/mark-all-read', { method: 'POST' }),
}
