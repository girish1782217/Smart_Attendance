import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'

import { AuthProvider } from './contexts/AuthContext'
import { ToastProvider } from './contexts/ToastContext'
import { AppShell } from './layouts/AppShell'
import { AdminDashboardPage } from './pages/admin/AdminDashboardPage'
import { FacultyDashboardPage } from './pages/faculty/FacultyDashboardPage'
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
                </Route>
              </Route>

              <Route element={<ProtectedRoute allowedRoles={['FACULTY']} />}>
                <Route element={<AppShell role="FACULTY" />}>
                  <Route path="/faculty" element={<FacultyDashboardPage />} />
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
