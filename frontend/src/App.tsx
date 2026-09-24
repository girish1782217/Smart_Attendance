import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'

import { AuthProvider } from './contexts/AuthContext'
import { ToastProvider } from './contexts/ToastContext'
import { AppShell } from './layouts/AppShell'
import { AcademicYearsPage } from './pages/admin/AcademicYearsPage'
import { AdminDashboardPage } from './pages/admin/AdminDashboardPage'
import { ClassesPage } from './pages/admin/ClassesPage'
import { DepartmentsPage } from './pages/admin/DepartmentsPage'
import { FacultyAssignmentsPage } from './pages/admin/FacultyAssignmentsPage'
import { FacultyPage } from './pages/admin/FacultyPage'
import { ProgramsPage } from './pages/admin/ProgramsPage'
import { SectionsPage } from './pages/admin/SectionsPage'
import { SemestersPage } from './pages/admin/SemestersPage'
import { StudentsPage } from './pages/admin/StudentsPage'
import { SubjectsPage } from './pages/admin/SubjectsPage'
import { FacultyDashboardPage } from './pages/faculty/FacultyDashboardPage'
import { FacultySessionDetailPage } from './pages/faculty/FacultySessionDetailPage'
import { FacultySessionsPage } from './pages/faculty/FacultySessionsPage'
import { HomeRedirect } from './pages/HomeRedirect'
import { LoginPage } from './pages/LoginPage'
import { StudentDashboardPage } from './pages/student/StudentDashboardPage'
import { ProtectedRoute } from './routes/ProtectedRoute'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { retry: 1 },
  },
})

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <ToastProvider>
        <BrowserRouter>
          <AuthProvider>
            <Routes>
              <Route path="/login" element={<LoginPage />} />
              <Route path="/" element={<HomeRedirect />} />

              <Route element={<ProtectedRoute allowedRoles={['ADMIN']} />}>
                <Route element={<AppShell role="ADMIN" />}>
                  <Route path="/admin" element={<AdminDashboardPage />} />
                  <Route path="/admin/departments" element={<DepartmentsPage />} />
                  <Route path="/admin/programs" element={<ProgramsPage />} />
                  <Route path="/admin/classes" element={<ClassesPage />} />
                  <Route path="/admin/sections" element={<SectionsPage />} />
                  <Route path="/admin/subjects" element={<SubjectsPage />} />
                  <Route path="/admin/academic-years" element={<AcademicYearsPage />} />
                  <Route path="/admin/semesters" element={<SemestersPage />} />
                  <Route path="/admin/students" element={<StudentsPage />} />
                  <Route path="/admin/faculty" element={<FacultyPage />} />
                  <Route path="/admin/faculty-assignments" element={<FacultyAssignmentsPage />} />
                </Route>
              </Route>

              <Route element={<ProtectedRoute allowedRoles={['FACULTY']} />}>
                <Route element={<AppShell role="FACULTY" />}>
                  <Route path="/faculty" element={<FacultyDashboardPage />} />
                  <Route path="/faculty/sessions" element={<FacultySessionsPage />} />
                  <Route path="/faculty/sessions/:sessionId" element={<FacultySessionDetailPage />} />
                </Route>
              </Route>

              <Route element={<ProtectedRoute allowedRoles={['STUDENT']} />}>
                <Route element={<AppShell role="STUDENT" />}>
                  <Route path="/student" element={<StudentDashboardPage />} />
                </Route>
              </Route>

              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </AuthProvider>
        </BrowserRouter>
      </ToastProvider>
    </QueryClientProvider>
  )
}

export default App
