import { NavLink, Outlet } from 'react-router-dom'

import { useAuth } from '../contexts/AuthContext'
import type { RoleName } from '../types/roles'

interface NavItem {
  to: string
  label: string
}

const NAV_ITEMS: Record<RoleName, NavItem[]> = {
  ADMIN: [
    { to: '/admin', label: 'Dashboard' },
    { to: '/admin/departments', label: 'Departments' },
    { to: '/admin/programs', label: 'Programs' },
    { to: '/admin/classes', label: 'Classes' },
    { to: '/admin/sections', label: 'Sections' },
    { to: '/admin/subjects', label: 'Subjects' },
    { to: '/admin/academic-years', label: 'Academic Years' },
    { to: '/admin/semesters', label: 'Semesters' },
    { to: '/admin/students', label: 'Students' },
    { to: '/admin/faculty', label: 'Faculty' },
    { to: '/admin/faculty-assignments', label: 'Assignments' },
    { to: '/admin/corrections', label: 'Corrections' },
    { to: '/admin/reports', label: 'Reports' },
    { to: '/admin/settings', label: 'Settings' },
  ],
  FACULTY: [
    { to: '/faculty', label: 'Dashboard' },
    { to: '/faculty/sessions', label: 'Attendance Sessions' },
    { to: '/faculty/corrections', label: 'Corrections' },
    { to: '/faculty/low-attendance', label: 'Low Attendance' },
  ],
  STUDENT: [
    { to: '/student', label: 'Dashboard' },
    { to: '/student/attendance', label: 'My Attendance' },
    { to: '/student/corrections', label: 'My Corrections' },
    { to: '/student/ai-insight', label: 'AI Insight' },
  ],
}

export function AppShell({ role }: { role: RoleName }) {
  const { user, logout } = useAuth()
  const navItems = NAV_ITEMS[role]

  return (
    <div className="flex min-h-screen bg-slate-50">
      <aside className="hidden w-64 flex-shrink-0 border-r border-slate-200 bg-white sm:block">
        <div className="border-b border-slate-200 px-4 py-4">
          <p className="text-sm font-semibold text-slate-900">Smart Attendance</p>
          <p className="text-xs text-slate-500">{role}</p>
        </div>
        <nav className="flex flex-col gap-1 p-2">
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === `/${role.toLowerCase()}`}
              className={({ isActive }) =>
                `rounded-md px-3 py-2 text-sm font-medium ${
                  isActive ? 'bg-slate-900 text-white' : 'text-slate-700 hover:bg-slate-100'
                }`
              }
            >
              {item.label}
            </NavLink>
          ))}
        </nav>
      </aside>

      <div className="flex min-w-0 flex-1 flex-col">
        <header className="flex items-center justify-between border-b border-slate-200 bg-white px-4 py-3 sm:px-6">
          <p className="text-sm text-slate-600">
            Signed in as <span className="font-medium text-slate-900">{user?.full_name}</span>
          </p>
          <button
            type="button"
            onClick={() => void logout()}
            className="rounded-md border border-slate-300 px-3 py-1.5 text-sm font-medium text-slate-700 hover:bg-slate-50"
          >
            Log out
          </button>
        </header>
        <main className="flex-1 overflow-auto p-4 sm:p-6">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
