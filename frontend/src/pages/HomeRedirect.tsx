import { Navigate } from 'react-router-dom'

import { LoadingState } from '../components/LoadingState'
import { useAuth } from '../contexts/AuthContext'

export function HomeRedirect() {
  const { user, isLoading } = useAuth()

  if (isLoading) return <LoadingState />
  if (!user) return <Navigate to="/login" replace />

  if (user.roles.includes('ADMIN')) return <Navigate to="/admin" replace />
  if (user.roles.includes('FACULTY')) return <Navigate to="/faculty" replace />
  if (user.roles.includes('STUDENT')) return <Navigate to="/student" replace />

  return <Navigate to="/login" replace />
}
