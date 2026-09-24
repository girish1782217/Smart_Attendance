import { useQuery } from '@tanstack/react-query'

import { getHealth } from '../api/health'

export function HealthStatus() {
  const { data, isLoading, isError } = useQuery({
    queryKey: ['health'],
    queryFn: getHealth,
  })

  if (isLoading) {
    return (
      <p role="status" className="text-sm text-slate-500">
        Checking backend connection…
      </p>
    )
  }

  if (isError || !data?.success) {
    return (
      <p role="alert" className="text-sm text-red-600">
        Backend unavailable.
      </p>
    )
  }

  return (
    <p role="status" className="text-sm text-emerald-600">
      Backend connected ({data.service}: {data.status}).
    </p>
  )
}
