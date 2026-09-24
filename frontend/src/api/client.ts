import { clearToken, getToken } from './tokenStore'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'

export class ApiError extends Error {
  readonly status: number
  readonly code: string

  constructor(message: string, status: number, code: string) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.code = code
  }
}

type ErrorEnvelope = { success: false; error: { code: string; message: string } }

const SESSION_INVALID_CODES = new Set(['TOKEN_EXPIRED', 'TOKEN_REVOKED', 'INVALID_TOKEN'])

/** Set by AuthContext so a 401 caused by an expired/revoked token can
 * redirect to /login, instead of every page having to handle it. */
let onSessionInvalid: (() => void) | null = null

export function registerSessionInvalidHandler(handler: () => void): void {
  onSessionInvalid = handler
}

/** Turns { page: 1, search: undefined, ... } into "?page=1" -- omitting
 * undefined/null/empty-string values so callers can pass optional filters
 * directly without each one conditionally building the query string. */
export function buildQueryString(params: Record<string, unknown>): string {
  const searchParams = new URLSearchParams()
  for (const [key, value] of Object.entries(params)) {
    if (value === undefined || value === null || value === '') continue
    searchParams.set(key, String(value))
  }
  const query = searchParams.toString()
  return query ? `?${query}` : ''
}

async function parseErrorBody(response: Response, path: string): Promise<ApiError> {
  let code = 'UNKNOWN_ERROR'
  let message = `Request to ${path} failed with status ${response.status}`
  try {
    const body = (await response.json()) as ErrorEnvelope
    code = body.error?.code ?? code
    message = body.error?.message ?? message
  } catch {
    // Response body wasn't JSON (or was empty) — fall back to the generic message above.
  }
  return new ApiError(message, response.status, code)
}

function authHeaders(): Record<string, string> {
  const token = getToken()
  return token ? { Authorization: `Bearer ${token}` } : {}
}

export async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: {
      'Content-Type': 'application/json',
      ...authHeaders(),
      ...init?.headers,
    },
  })

  if (!response.ok) {
    const error = await parseErrorBody(response, path)
    if (response.status === 401 && SESSION_INVALID_CODES.has(error.code)) {
      clearToken()
      onSessionInvalid?.()
    }
    throw error
  }

  if (response.status === 204) {
    return undefined as T
  }
  return (await response.json()) as T
}

/** For CSV export endpoints, which return text/csv rather than JSON. */
export async function apiFetchBlob(path: string): Promise<Blob> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: { ...authHeaders() },
  })
  if (!response.ok) {
    throw await parseErrorBody(response, path)
  }
  return await response.blob()
}
