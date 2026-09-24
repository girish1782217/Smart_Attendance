import { useQueryClient } from '@tanstack/react-query'
import { createContext, useCallback, useContext, useEffect, useState, type ReactNode } from 'react'

import { getCurrentUser, login as apiLogin, logout as apiLogout, type CurrentUser } from '../api/auth'
import { registerSessionInvalidHandler } from '../api/client'
import { clearToken, getToken, setToken } from '../api/tokenStore'
import type { RoleName } from '../types/roles'

interface AuthContextValue {
  user: CurrentUser | null
  isLoading: boolean
  isAuthenticated: boolean
  login: (email: string, password: string) => Promise<void>
  logout: () => Promise<void>
  hasRole: (role: RoleName) => boolean
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<CurrentUser | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const queryClient = useQueryClient()

  const clearSession = useCallback(() => {
    clearToken()
    setUser(null)
    queryClient.clear()
  }, [queryClient])

  // Wired once so any API call anywhere in the app that hits a
  // token-expired/revoked 401 drops the user back to a logged-out state,
  // instead of every page having to handle that case individually.
  useEffect(() => {
    registerSessionInvalidHandler(clearSession)
  }, [clearSession])

  useEffect(() => {
    const token = getToken()
    if (!token) {
      setIsLoading(false)
      return
    }
    getCurrentUser()
      .then(setUser)
      .catch(() => {
        clearToken()
        setUser(null)
      })
      .finally(() => setIsLoading(false))
  }, [])

  const login = useCallback(async (email: string, password: string) => {
    const { access_token } = await apiLogin({ email, password })
    setToken(access_token)
    const currentUser = await getCurrentUser()
    setUser(currentUser)
  }, [])

  const logout = useCallback(async () => {
    try {
      await apiLogout()
    } catch {
      // Best-effort -- clear local state regardless of whether the
      // server-side revocation call succeeded.
    }
    clearSession()
  }, [clearSession])

  const hasRole = useCallback((role: RoleName) => user?.roles.includes(role) ?? false, [user])

  return (
    <AuthContext.Provider
      value={{ user, isLoading, isAuthenticated: user !== null, login, logout, hasRole }}
    >
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}
