import { apiFetch } from './client'
import type { RoleName } from '../types/roles'

export interface LoginRequest {
  email: string
  password: string
}

export interface TokenResponse {
  access_token: string
  token_type: string
}

export interface CurrentUser {
  id: number
  email: string
  full_name: string
  is_active: boolean
  created_at: string
  roles: RoleName[]
}

export function login(payload: LoginRequest): Promise<TokenResponse> {
  return apiFetch<TokenResponse>('/api/v1/auth/login', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export function logout(): Promise<{ success: boolean; message: string }> {
  return apiFetch('/api/v1/auth/logout', { method: 'POST' })
}

export function getCurrentUser(): Promise<CurrentUser> {
  return apiFetch<CurrentUser>('/api/v1/auth/me')
}
