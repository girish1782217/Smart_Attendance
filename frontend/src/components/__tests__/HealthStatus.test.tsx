import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, waitFor } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { HealthStatus } from '../HealthStatus'

function renderWithQueryClient(ui: React.ReactElement) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  })
  return render(<QueryClientProvider client={queryClient}>{ui}</QueryClientProvider>)
}

describe('HealthStatus', () => {
  beforeEach(() => {
    vi.stubGlobal('fetch', vi.fn())
  })

  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('shows a connected message when the backend is healthy', async () => {
    vi.mocked(fetch).mockResolvedValueOnce(
      new Response(
        JSON.stringify({ success: true, status: 'ok', service: 'smart-attendance-backend' }),
        { status: 200 },
      ),
    )

    renderWithQueryClient(<HealthStatus />)

    expect(screen.getByRole('status')).toHaveTextContent('Checking backend connection')

    await waitFor(() =>
      expect(screen.getByRole('status')).toHaveTextContent('Backend connected'),
    )
  })

  it('shows an error message when the backend is unavailable', async () => {
    vi.mocked(fetch).mockResolvedValueOnce(
      new Response(
        JSON.stringify({ success: false, error: { code: 'DOWN', message: 'down' } }),
        { status: 503 },
      ),
    )

    renderWithQueryClient(<HealthStatus />)

    await waitFor(() => expect(screen.getByRole('alert')).toHaveTextContent('Backend unavailable'))
  })
})
