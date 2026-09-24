import { Navigate, Outlet } from 'react-router-dom'

import { useAuth } from '../contexts/AuthContext'
import { LoadingState } from '../components/LoadingState'
import type { RoleName } from '../types/roles'

export function ProtectedRoute({ allowedRoles }: { allowedRoles: RoleName[] }) {
  const { isAuthenticated, isLoading, user } = useAuth()

  if (isLoading) {
    return <LoadingState label="Checking your session…" />
  }

  if (!isAuthenticated || !user) {
    return <Navigate to="/login" replace />
  }

  const isAllowed = allowedRoles.some((role) => user.roles.includes(role))
  if (!isAllowed) {
    return <Navigate to="/" replace />
  }

  return <Outlet />
}
