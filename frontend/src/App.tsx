import { QueryClient, QueryClientProvider } from '@tanstack/react-query'

import { HealthStatus } from './components/HealthStatus'

const queryClient = new QueryClient()

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <div className="min-h-screen bg-slate-50 p-8">
        <h1 className="text-2xl font-semibold text-slate-900">
          Smart Attendance Management System
        </h1>
        <p className="mt-1 text-slate-600">Project foundation — SPEC 01.</p>
        <div className="mt-4">
          <HealthStatus />
        </div>
      </div>
    </QueryClientProvider>
  )
}

export default App
