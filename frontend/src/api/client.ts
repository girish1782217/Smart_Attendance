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

export async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: {
      'Content-Type': 'application/json',
      ...init?.headers,
    },
  })

  if (!response.ok) {
    let code = 'UNKNOWN_ERROR'
    let message = `Request to ${path} failed with status ${response.status}`
    try {
      const body = (await response.json()) as ErrorEnvelope
      code = body.error?.code ?? code
      message = body.error?.message ?? message
    } catch {
      // Response body wasn't JSON (or was empty) — fall back to the generic message above.
    }
    throw new ApiError(message, response.status, code)
  }

  return (await response.json()) as T
}
