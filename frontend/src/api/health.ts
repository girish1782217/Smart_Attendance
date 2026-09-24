import { apiFetch } from './client'

export interface HealthResponse {
  success: boolean
  status: string
  service: string
}

export function getHealth(): Promise<HealthResponse> {
  return apiFetch<HealthResponse>('/health')
}
