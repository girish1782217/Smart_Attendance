import { useQuery, useQueryClient } from '@tanstack/react-query'
import { Bell } from 'lucide-react'
import { useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'

import { notificationsApi, type Notification } from '../api/notifications'
import type { RoleName } from '../types/roles'

function targetPathFor(role: RoleName, notification: Notification): string | null {
  if (notification.type.startsWith('CORRECTION_')) {
    return `/${role.toLowerCase()}/corrections`
  }
  if (notification.type === 'LOW_ATTENDANCE_WARNING') {
    if (role === 'STUDENT') return '/student/attendance'
    if (role === 'FACULTY') return '/faculty/low-attendance'
    return '/admin/reports'
  }
  return null
}

export function NotificationsBell({ role }: { role: RoleName }) {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [isOpen, setIsOpen] = useState(false)
  const containerRef = useRef<HTMLDivElement>(null)

  const { data: unread } = useQuery({
    queryKey: ['notifications', 'unread-count'],
    queryFn: notificationsApi.getUnreadCount,
    refetchInterval: 30_000,
  })

  const { data: list } = useQuery({
    queryKey: ['notifications', 'recent'],
    queryFn: () => notificationsApi.list({ page: 1, page_size: 10 }),
    enabled: isOpen,
  })

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setIsOpen(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  async function handleSelect(notification: Notification) {
    if (!notification.is_read) {
      await notificationsApi.markRead(notification.id)
      await queryClient.invalidateQueries({ queryKey: ['notifications'] })
    }
    setIsOpen(false)
    const target = targetPathFor(role, notification)
    if (target) navigate(target)
  }

  async function handleMarkAllRead() {
    await notificationsApi.markAllRead()
    await queryClient.invalidateQueries({ queryKey: ['notifications'] })
  }

  const count = unread?.count ?? 0

  return (
    <div className="relative" ref={containerRef}>
      <button
        type="button"
        aria-label="Notifications"
        onClick={() => setIsOpen((open) => !open)}
        className="relative flex h-9 w-9 items-center justify-center rounded-full text-slate-500 transition hover:bg-slate-100 hover:text-slate-700"
      >
        <Bell className="h-5 w-5" strokeWidth={2} />
        {count > 0 && (
          <span className="absolute right-1 top-1 flex h-4 min-w-4 items-center justify-center rounded-full bg-red-600 px-1 text-[10px] font-semibold leading-none text-white">
            {count > 9 ? '9+' : count}
          </span>
        )}
      </button>

      {isOpen && (
        <div className="absolute right-0 top-12 z-50 w-80 overflow-hidden rounded-xl border border-slate-200 bg-white shadow-lg ring-1 ring-black/5">
          <div className="flex items-center justify-between border-b border-slate-100 px-4 py-3">
            <p className="text-sm font-semibold text-slate-900">Notifications</p>
            <button
              type="button"
              onClick={() => void handleMarkAllRead()}
              className="text-xs font-medium text-brand-600 hover:text-brand-700 hover:underline"
            >
              Mark all read
            </button>
          </div>
          <div className="max-h-96 overflow-y-auto">
            {list && list.items.length === 0 && (
              <p className="px-4 py-6 text-center text-sm text-slate-500">No notifications yet.</p>
            )}
            {list?.items.map((notification) => (
              <button
                key={notification.id}
                type="button"
                onClick={() => void handleSelect(notification)}
                className={`block w-full border-b border-slate-100 px-4 py-3 text-left last:border-0 hover:bg-slate-50 ${
                  notification.is_read ? '' : 'bg-brand-50/60'
                }`}
              >
                <p className="text-sm font-medium text-slate-900">{notification.title}</p>
                <p className="mt-0.5 line-clamp-2 text-xs text-slate-500">{notification.message}</p>
                <p className="mt-1 text-xs text-slate-400">{new Date(notification.created_at).toLocaleString()}</p>
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
