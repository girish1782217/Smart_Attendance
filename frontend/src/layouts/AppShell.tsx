import {
  AlertTriangle,
  BarChart3,
  Bell,
  Building2,
  CalendarCheck,
  CalendarRange,
  ClipboardCheck,
  ClipboardList,
  FileEdit,
  GraduationCap,
  LayoutDashboard,
  LogOut,
  Settings,
  Sparkles,
  UserCog,
  Users,
  type LucideIcon,
} from 'lucide-react'
import { NavLink, Outlet } from 'react-router-dom'

import { useAuth } from '../contexts/AuthContext'
import type { RoleName } from '../types/roles'

interface NavItem {
  to: string
  label: string
  icon: LucideIcon
}

const NAV_ITEMS: Record<RoleName, NavItem[]> = {
  ADMIN: [
    { to: '/admin', label: 'Dashboard', icon: LayoutDashboard },
    { to: '/admin/departments', label: 'Departments', icon: Building2 },
    { to: '/admin/programs', label: 'Programs', icon: GraduationCap },
    { to: '/admin/classes', label: 'Classes', icon: Users },
    { to: '/admin/sections', label: 'Sections', icon: Users },
    { to: '/admin/subjects', label: 'Subjects', icon: ClipboardList },
    { to: '/admin/academic-years', label: 'Academic Years', icon: CalendarRange },
    { to: '/admin/semesters', label: 'Semesters', icon: CalendarRange },
    { to: '/admin/students', label: 'Students', icon: GraduationCap },
    { to: '/admin/faculty', label: 'Faculty', icon: UserCog },
    { to: '/admin/faculty-assignments', label: 'Assignments', icon: ClipboardCheck },
    { to: '/admin/corrections', label: 'Corrections', icon: FileEdit },
    { to: '/admin/reports', label: 'Reports', icon: BarChart3 },
    { to: '/admin/settings', label: 'Settings', icon: Settings },
  ],
  FACULTY: [
    { to: '/faculty', label: 'Dashboard', icon: LayoutDashboard },
    { to: '/faculty/sessions', label: 'Attendance Sessions', icon: ClipboardCheck },
    { to: '/faculty/corrections', label: 'Corrections', icon: FileEdit },
    { to: '/faculty/low-attendance', label: 'Low Attendance', icon: AlertTriangle },
  ],
  STUDENT: [
    { to: '/student', label: 'Dashboard', icon: LayoutDashboard },
    { to: '/student/attendance', label: 'My Attendance', icon: CalendarCheck },
    { to: '/student/corrections', label: 'My Corrections', icon: FileEdit },
    { to: '/student/ai-insight', label: 'AI Insight', icon: Sparkles },
  ],
}

const ROLE_LABEL: Record<RoleName, string> = {
  ADMIN: 'Administrator',
  FACULTY: 'Faculty',
  STUDENT: 'Student',
}

function initialsOf(fullName: string): string {
  const parts = fullName.trim().split(/\s+/)
  const initials = parts.length === 1 ? parts[0]!.slice(0, 2) : `${parts[0]![0]}${parts[parts.length - 1]![0]}`
  return initials.toUpperCase()
}

export function AppShell({ role }: { role: RoleName }) {
  const { user, logout } = useAuth()
  const navItems = NAV_ITEMS[role]

  return (
    <div className="flex min-h-screen bg-slate-50">
      <aside className="hidden w-64 flex-shrink-0 flex-col border-r border-slate-200 bg-white sm:flex">
        <div className="flex items-center gap-2.5 border-b border-slate-100 px-5 py-5">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-brand-600 text-white">
            <GraduationCap className="h-5 w-5" strokeWidth={2} />
          </div>
          <div className="min-w-0">
            <p className="truncate text-sm font-semibold text-slate-900">Smart Attendance</p>
            <p className="text-xs text-slate-400">{ROLE_LABEL[role]}</p>
          </div>
        </div>

        <nav className="flex flex-1 flex-col gap-0.5 overflow-y-auto p-3">
          {navItems.map((item) => {
            const Icon = item.icon
            return (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.to === `/${role.toLowerCase()}`}
                className={({ isActive }) =>
                  `flex items-center gap-2.5 rounded-lg px-3 py-2 text-sm font-medium transition ${
                    isActive
                      ? 'bg-brand-50 text-brand-700'
                      : 'text-slate-600 hover:bg-slate-50 hover:text-slate-900'
                  }`
                }
              >
                <Icon className="h-4 w-4 flex-shrink-0" strokeWidth={2} />
                <span className="truncate">{item.label}</span>
              </NavLink>
            )
          })}
        </nav>
      </aside>

      <div className="flex min-w-0 flex-1 flex-col">
        <header className="flex items-center justify-between border-b border-slate-200 bg-white px-4 py-3 sm:px-6">
          <div className="sm:hidden">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-brand-600 text-white">
              <GraduationCap className="h-[18px] w-[18px]" strokeWidth={2} />
            </div>
          </div>
          <div className="hidden sm:block" />

          <div className="flex items-center gap-4">
            <button
              type="button"
              aria-label="Notifications"
              className="relative flex h-9 w-9 items-center justify-center rounded-full text-slate-500 transition hover:bg-slate-100 hover:text-slate-700"
            >
              <Bell className="h-5 w-5" strokeWidth={2} />
            </button>

            <div className="flex items-center gap-3 border-l border-slate-200 pl-4">
              <div className="hidden text-right sm:block">
                <p className="text-sm font-medium leading-tight text-slate-900">{user?.full_name}</p>
                <p className="text-xs leading-tight text-slate-400">{user?.email}</p>
              </div>
              <div className="flex h-9 w-9 flex-shrink-0 items-center justify-center rounded-full bg-brand-100 text-sm font-semibold text-brand-700">
                {user ? initialsOf(user.full_name) : ''}
              </div>
              <button
                type="button"
                onClick={() => void logout()}
                aria-label="Log out"
                title="Log out"
                className="flex h-9 w-9 items-center justify-center rounded-full text-slate-500 transition hover:bg-slate-100 hover:text-slate-700"
              >
                <LogOut className="h-[18px] w-[18px]" strokeWidth={2} />
              </button>
            </div>
          </div>
        </header>
        <main className="flex-1 overflow-auto p-4 sm:p-6">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
